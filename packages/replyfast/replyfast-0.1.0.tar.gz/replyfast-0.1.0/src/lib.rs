use std::path::PathBuf;
use std::time::UNIX_EPOCH;

use base64::engine::general_purpose::STANDARD as BASE64;
use base64::Engine;
use futures::{channel::oneshot, future, pin_mut, StreamExt};
use pyo3::exceptions::PyRuntimeError;
use pyo3::prelude::*;
use pyo3::types::PyAny;

use presage::libsignal_service::configuration::SignalServers;
use presage::libsignal_service::content::{Content, ContentBody, DataMessage};
use presage::libsignal_service::prelude::Uuid;
use presage::libsignal_service::protocol::ServiceId;
use presage::model::contacts::Contact as PresageContact;
use presage::model::groups::Group as PresageGroup;
use presage::model::messages::Received;
use presage::store::ContentsStore;
use presage::Manager;
use presage_store_sqlite::{OnNewIdentity, SqliteStore};

/// Initialize tracing for debugging
fn init_tracing() {
    use tracing_subscriber::{fmt, prelude::*, EnvFilter};
    let _ = tracing_subscriber::registry()
        .with(fmt::layer())
        .with(EnvFilter::from_default_env())
        .try_init();
}

/// A received message from Signal
#[pyclass]
#[derive(Clone)]
pub struct Message {
    #[pyo3(get)]
    pub sender: String,
    #[pyo3(get)]
    pub body: Option<String>,
    #[pyo3(get)]
    pub timestamp: u64,
    #[pyo3(get)]
    pub group_id: Option<String>,
    #[pyo3(get)]
    pub is_read_receipt: bool,
    #[pyo3(get)]
    pub is_typing_indicator: bool,
    #[pyo3(get)]
    pub is_queue_empty: bool,
}

#[pymethods]
impl Message {
    fn __repr__(&self) -> String {
        format!(
            "Message(sender='{}', body={:?}, timestamp={}, group_id={:?})",
            self.sender, self.body, self.timestamp, self.group_id
        )
    }
}

/// A Signal contact
#[pyclass]
#[derive(Clone)]
pub struct Contact {
    #[pyo3(get)]
    pub uuid: String,
    #[pyo3(get)]
    pub name: Option<String>,
    #[pyo3(get)]
    pub phone_number: Option<String>,
}

#[pymethods]
impl Contact {
    fn __repr__(&self) -> String {
        format!(
            "Contact(uuid='{}', name={:?}, phone_number={:?})",
            self.uuid, self.name, self.phone_number
        )
    }
}

/// A Signal group
#[pyclass]
#[derive(Clone)]
pub struct Group {
    #[pyo3(get)]
    pub id: String,
    #[pyo3(get)]
    pub title: String,
    #[pyo3(get)]
    pub members: Vec<String>,
}

#[pymethods]
impl Group {
    fn __repr__(&self) -> String {
        format!(
            "Group(id='{}', title='{}', members={:?})",
            self.id, self.title, self.members
        )
    }
}

/// Account information
#[pyclass]
#[derive(Clone)]
pub struct AccountInfo {
    #[pyo3(get)]
    pub uuid: String,
    #[pyo3(get)]
    pub phone_number: String,
    #[pyo3(get)]
    pub device_id: Option<u32>,
}

#[pymethods]
impl AccountInfo {
    fn __repr__(&self) -> String {
        format!(
            "AccountInfo(uuid='{}', phone_number='{}', device_id={:?})",
            self.uuid, self.phone_number, self.device_id
        )
    }
}

/// Convert Content to our Message type
fn content_to_message(content: &Content) -> Option<Message> {
    let sender = content.metadata.sender.raw_uuid().to_string();
    let timestamp = content.metadata.timestamp;

    match &content.body {
        ContentBody::DataMessage(dm) => {
            let group_id = dm
                .group_v2
                .as_ref()
                .and_then(|g| g.master_key.as_ref())
                .map(|k| BASE64.encode(k));

            Some(Message {
                sender,
                body: dm.body.clone(),
                timestamp,
                group_id,
                is_read_receipt: false,
                is_typing_indicator: false,
                is_queue_empty: false,
            })
        }
        ContentBody::SynchronizeMessage(sync) => {
            if let Some(sent) = &sync.sent {
                if let Some(dm) = &sent.message {
                    let group_id = dm
                        .group_v2
                        .as_ref()
                        .and_then(|g| g.master_key.as_ref())
                        .map(|k| BASE64.encode(k));
                    return Some(Message {
                        sender,
                        body: dm.body.clone(),
                        timestamp,
                        group_id,
                        is_read_receipt: false,
                        is_typing_indicator: false,
                        is_queue_empty: false,
                    });
                }
            }
            None
        }
        ContentBody::ReceiptMessage(_) => Some(Message {
            sender,
            body: None,
            timestamp,
            group_id: None,
            is_read_receipt: true,
            is_typing_indicator: false,
            is_queue_empty: false,
        }),
        ContentBody::TypingMessage(_) => Some(Message {
            sender,
            body: None,
            timestamp,
            group_id: None,
            is_read_receipt: false,
            is_typing_indicator: true,
            is_queue_empty: false,
        }),
        _ => None,
    }
}

/// Helper to run async code that may not be Send
fn run_local_async<F, T>(fut: F) -> Result<T, String>
where
    F: std::future::Future<Output = Result<T, String>>,
{
    let rt = tokio::runtime::Builder::new_current_thread()
        .enable_all()
        .build()
        .map_err(|e| format!("Failed to create runtime: {e}"))?;

    rt.block_on(fut)
}

/// Signal client for sending and receiving messages
#[pyclass]
pub struct SignalClient {
    db_path: String,
}

#[pymethods]
impl SignalClient {
    /// Create a new Signal client
    ///
    /// Args:
    ///     data_path: Path to store Signal data (will create signal.db inside)
    #[new]
    fn new(data_path: &str) -> PyResult<Self> {
        init_tracing();
        let path = PathBuf::from(data_path);
        std::fs::create_dir_all(&path)
            .map_err(|e| PyRuntimeError::new_err(format!("Failed to create data dir: {e}")))?;

        let db_path = format!("sqlite://{}?mode=rwc", path.join("signal.db").display());

        Ok(Self { db_path })
    }

    /// Check if client is registered (sync version)
    fn is_registered_sync(&self) -> PyResult<bool> {
        let db_path = self.db_path.clone();

        run_local_async(async move {
            let store = match SqliteStore::open(&db_path, OnNewIdentity::Trust).await {
                Ok(s) => s,
                Err(_) => return Ok(false),
            };

            match Manager::load_registered(store).await {
                Ok(_) => Ok(true),
                Err(_) => Ok(false),
            }
        })
        .map_err(|e| PyRuntimeError::new_err(e))
    }

    /// Link as a secondary device (sync, blocking)
    ///
    /// Args:
    ///     device_name: Name for this device
    ///     callback: Optional Python callable that receives the URL for QR code
    ///
    /// This function blocks until the device is linked.
    fn link_device_sync(
        &self,
        py: Python<'_>,
        device_name: &str,
        url_callback: Option<Py<PyAny>>,
    ) -> PyResult<()> {
        let db_path = self.db_path.clone();
        let device_name = device_name.to_string();

        // Release GIL while doing blocking I/O
        py.detach(|| {
            run_local_async(async move {
                let store = SqliteStore::open(&db_path, OnNewIdentity::Trust)
                    .await
                    .map_err(|e| format!("Failed to open store: {e}"))?;

                let (provisioning_link_tx, provisioning_link_rx) = oneshot::channel();

                // Run linking and URL receiving concurrently
                let (link_result, _) = future::join(
                    Manager::link_secondary_device(
                        store,
                        SignalServers::Production,
                        device_name,
                        provisioning_link_tx,
                    ),
                    async {
                        if let Ok(url) = provisioning_link_rx.await {
                            let url_str = url.to_string();
                            println!("Provisioning URL: {}", url_str);

                            // Call the Python callback if provided
                            if let Some(cb) = url_callback {
                                Python::attach(|py| {
                                    let _ = cb.call1(py, (url_str,));
                                });
                            }
                        }
                    },
                )
                .await;

                link_result.map_err(|e| format!("Linking failed: {e}"))?;
                Ok(())
            })
        })
        .map_err(|e| PyRuntimeError::new_err(e))
    }

    /// Send a message to a recipient (sync, blocking)
    ///
    /// Args:
    ///     recipient: UUID of the recipient
    ///     message: Text message to send
    fn send_message_sync(&self, py: Python<'_>, recipient: &str, message: &str) -> PyResult<()> {
        let db_path = self.db_path.clone();
        let recipient = recipient.to_string();
        let message = message.to_string();

        py.detach(|| {
            run_local_async(async move {
                let store = SqliteStore::open(&db_path, OnNewIdentity::Trust)
                    .await
                    .map_err(|e| format!("Failed to open store: {e}"))?;

                let mut manager = Manager::load_registered(store)
                    .await
                    .map_err(|e| format!("Not registered: {e}"))?;

                // Parse recipient UUID
                let recipient_uuid: Uuid = recipient
                    .parse()
                    .map_err(|e| format!("Invalid UUID: {e}"))?;

                let service_id = ServiceId::Aci(recipient_uuid.into());

                // Create timestamp
                let timestamp = std::time::SystemTime::now()
                    .duration_since(UNIX_EPOCH)
                    .expect("Time went backwards")
                    .as_millis() as u64;

                // Create data message and wrap in ContentBody
                let data_message = DataMessage {
                    body: Some(message),
                    timestamp: Some(timestamp),
                    ..Default::default()
                };
                let content_body = ContentBody::DataMessage(data_message);

                // Send the message
                manager
                    .send_message(service_id, content_body, timestamp)
                    .await
                    .map_err(|e| format!("Failed to send: {e}"))?;

                Ok(())
            })
        })
        .map_err(|e| PyRuntimeError::new_err(e))
    }

    /// Send a message to a group (sync, blocking)
    ///
    /// Args:
    ///     group_id: Base64-encoded group master key
    ///     message: Text message to send
    fn send_group_message_sync(
        &self,
        py: Python<'_>,
        group_id: &str,
        message: &str,
    ) -> PyResult<()> {
        let db_path = self.db_path.clone();
        let group_id = group_id.to_string();
        let message = message.to_string();

        py.detach(|| {
            run_local_async(async move {
                let store = SqliteStore::open(&db_path, OnNewIdentity::Trust)
                    .await
                    .map_err(|e| format!("Failed to open store: {e}"))?;

                let mut manager = Manager::load_registered(store)
                    .await
                    .map_err(|e| format!("Not registered: {e}"))?;

                // Decode group master key
                let master_key_bytes = BASE64
                    .decode(&group_id)
                    .map_err(|e| format!("Invalid group ID: {e}"))?;

                let master_key: [u8; 32] = master_key_bytes
                    .try_into()
                    .map_err(|_| "Group ID must be 32 bytes".to_string())?;

                // Create timestamp
                let timestamp = std::time::SystemTime::now()
                    .duration_since(UNIX_EPOCH)
                    .expect("Time went backwards")
                    .as_millis() as u64;

                // Create data message and wrap in ContentBody
                let data_message = DataMessage {
                    body: Some(message),
                    timestamp: Some(timestamp),
                    ..Default::default()
                };
                let content_body = ContentBody::DataMessage(data_message);

                // Send to group
                manager
                    .send_message_to_group(&master_key, content_body, timestamp)
                    .await
                    .map_err(|e| format!("Failed to send: {e}"))?;

                Ok(())
            })
        })
        .map_err(|e| PyRuntimeError::new_err(e))
    }

    /// Receive messages (sync, blocking)
    ///
    /// Args:
    ///     callback: Python callable that receives Message objects.
    ///               Return True from callback to continue, False to stop.
    ///
    /// This will block and call the callback for each received message.
    fn receive_messages_sync(&self, py: Python<'_>, callback: Py<PyAny>) -> PyResult<()> {
        let db_path = self.db_path.clone();

        py.detach(|| {
            run_local_async(async move {
                let store = SqliteStore::open(&db_path, OnNewIdentity::Trust)
                    .await
                    .map_err(|e| format!("Failed to open store: {e}"))?;

                let mut manager = Manager::load_registered(store)
                    .await
                    .map_err(|e| format!("Not registered: {e}"))?;

                // Receive messages
                let messages = manager
                    .receive_messages()
                    .await
                    .map_err(|e| format!("Failed to receive: {e}"))?;
                pin_mut!(messages);

                // Process messages
                while let Some(received) = messages.next().await {
                    let msg = match received {
                        Received::QueueEmpty => Message {
                            sender: String::new(),
                            body: None,
                            timestamp: 0,
                            group_id: None,
                            is_read_receipt: false,
                            is_typing_indicator: false,
                            is_queue_empty: true,
                        },
                        Received::Contacts => continue,
                        Received::Content(content) => {
                            if let Some(msg) = content_to_message(&content) {
                                msg
                            } else {
                                continue;
                            }
                        }
                    };

                    // Call Python callback
                    let should_continue = Python::attach(|py| {
                        match callback.call1(py, (msg,)) {
                            Ok(result) => result.extract::<bool>(py).unwrap_or(true),
                            Err(_) => false,
                        }
                    });

                    if !should_continue {
                        break;
                    }
                }

                Ok(())
            })
        })
        .map_err(|e| PyRuntimeError::new_err(e))
    }

    /// Get synchronized contacts (sync)
    fn get_contacts_sync(&self, py: Python<'_>) -> PyResult<Vec<Contact>> {
        let db_path = self.db_path.clone();

        py.detach(|| {
            run_local_async(async move {
                let store = SqliteStore::open(&db_path, OnNewIdentity::Trust)
                    .await
                    .map_err(|e| format!("Failed to open store: {e}"))?;

                let manager = Manager::load_registered(store)
                    .await
                    .map_err(|e| format!("Not registered: {e}"))?;

                // Get contacts from store
                let contacts_iter = manager
                    .store()
                    .contacts()
                    .await
                    .map_err(|e| format!("Failed to get contacts: {e}"))?;

                let contacts: Vec<Contact> = contacts_iter
                    .filter_map(|c: Result<PresageContact, _>| c.ok())
                    .map(|c| Contact {
                        uuid: c.uuid.to_string(),
                        name: Some(c.name.clone()),
                        phone_number: c.phone_number.as_ref().map(|p| p.to_string()),
                    })
                    .collect();

                Ok(contacts)
            })
        })
        .map_err(|e| PyRuntimeError::new_err(e))
    }

    /// Get groups (sync)
    fn get_groups_sync(&self, py: Python<'_>) -> PyResult<Vec<Group>> {
        let db_path = self.db_path.clone();

        py.detach(|| {
            run_local_async(async move {
                let store = SqliteStore::open(&db_path, OnNewIdentity::Trust)
                    .await
                    .map_err(|e| format!("Failed to open store: {e}"))?;

                let manager = Manager::load_registered(store)
                    .await
                    .map_err(|e| format!("Not registered: {e}"))?;

                // Get groups from store
                let groups_iter = manager
                    .store()
                    .groups()
                    .await
                    .map_err(|e| format!("Failed to get groups: {e}"))?;

                let groups: Vec<Group> = groups_iter
                    .filter_map(|g: Result<([u8; 32], PresageGroup), _>| g.ok())
                    .map(|(key, group)| Group {
                        id: BASE64.encode(&key),
                        title: group.title,
                        members: group.members.iter().map(|m| m.aci.service_id_string()).collect(),
                    })
                    .collect();

                Ok(groups)
            })
        })
        .map_err(|e| PyRuntimeError::new_err(e))
    }

    /// Find a contact by phone number (from local synced contacts)
    ///
    /// Args:
    ///     phone: Phone number to search for (e.g., "+1234567890")
    ///
    /// Returns:
    ///     Contact if found, None otherwise
    fn find_contact_by_phone_sync(
        &self,
        py: Python<'_>,
        phone: &str,
    ) -> PyResult<Option<Contact>> {
        let db_path = self.db_path.clone();
        let phone = phone.to_string();

        py.detach(|| {
            run_local_async(async move {
                let store = SqliteStore::open(&db_path, OnNewIdentity::Trust)
                    .await
                    .map_err(|e| format!("Failed to open store: {e}"))?;

                let manager = Manager::load_registered(store)
                    .await
                    .map_err(|e| format!("Not registered: {e}"))?;

                let contacts_iter = manager
                    .store()
                    .contacts()
                    .await
                    .map_err(|e| format!("Failed to get contacts: {e}"))?;

                for contact in contacts_iter.filter_map(|c: Result<PresageContact, _>| c.ok()) {
                    if let Some(ref contact_phone) = contact.phone_number {
                        // Compare phone numbers (normalize by removing spaces/dashes)
                        let normalized_search: String =
                            phone.chars().filter(|c| c.is_ascii_digit() || *c == '+').collect();
                        let normalized_contact: String = contact_phone
                            .to_string()
                            .chars()
                            .filter(|c| c.is_ascii_digit() || *c == '+')
                            .collect();

                        if normalized_search == normalized_contact {
                            return Ok(Some(Contact {
                                uuid: contact.uuid.to_string(),
                                name: Some(contact.name.clone()),
                                phone_number: Some(contact_phone.to_string()),
                            }));
                        }
                    }
                }

                Ok(None)
            })
        })
        .map_err(|e| PyRuntimeError::new_err(e))
    }

    /// Find contacts by name (from local synced contacts)
    ///
    /// Args:
    ///     name: Name to search for (case-insensitive partial match)
    ///
    /// Returns:
    ///     List of matching contacts
    fn find_contacts_by_name_sync(
        &self,
        py: Python<'_>,
        name: &str,
    ) -> PyResult<Vec<Contact>> {
        let db_path = self.db_path.clone();
        let name = name.to_lowercase();

        py.detach(|| {
            run_local_async(async move {
                let store = SqliteStore::open(&db_path, OnNewIdentity::Trust)
                    .await
                    .map_err(|e| format!("Failed to open store: {e}"))?;

                let manager = Manager::load_registered(store)
                    .await
                    .map_err(|e| format!("Not registered: {e}"))?;

                let contacts_iter = manager
                    .store()
                    .contacts()
                    .await
                    .map_err(|e| format!("Failed to get contacts: {e}"))?;

                let matches: Vec<Contact> = contacts_iter
                    .filter_map(|c: Result<PresageContact, _>| c.ok())
                    .filter(|c| c.name.to_lowercase().contains(&name))
                    .map(|c| Contact {
                        uuid: c.uuid.to_string(),
                        name: Some(c.name.clone()),
                        phone_number: c.phone_number.as_ref().map(|p| p.to_string()),
                    })
                    .collect();

                Ok(matches)
            })
        })
        .map_err(|e| PyRuntimeError::new_err(e))
    }

    /// Get account information (sync)
    fn whoami_sync(&self, py: Python<'_>) -> PyResult<AccountInfo> {
        let db_path = self.db_path.clone();

        py.detach(|| {
            run_local_async(async move {
                let store = SqliteStore::open(&db_path, OnNewIdentity::Trust)
                    .await
                    .map_err(|e| format!("Failed to open store: {e}"))?;

                let manager = Manager::load_registered(store)
                    .await
                    .map_err(|e| format!("Not registered: {e}"))?;

                let data = manager.registration_data();

                Ok(AccountInfo {
                    uuid: data.service_ids.aci.to_string(),
                    phone_number: data.phone_number.to_string(),
                    device_id: data.device_id,
                })
            })
        })
        .map_err(|e| PyRuntimeError::new_err(e))
    }
}

/// Python module definition
#[pymodule]
fn _replyfast(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<SignalClient>()?;
    m.add_class::<Message>()?;
    m.add_class::<Contact>()?;
    m.add_class::<Group>()?;
    m.add_class::<AccountInfo>()?;
    Ok(())
}
