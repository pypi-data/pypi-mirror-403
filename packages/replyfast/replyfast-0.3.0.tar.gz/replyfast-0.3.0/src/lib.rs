use std::path::PathBuf;
use std::sync::atomic::{AtomicBool, Ordering};
use std::sync::{Arc, Mutex};
use std::time::UNIX_EPOCH;

use signal_hook::consts::SIGINT;
use signal_hook::flag as signal_flag;

use base64::engine::general_purpose::STANDARD as BASE64;
use base64::Engine;
use futures::{channel::oneshot, future, pin_mut, StreamExt};
use pyo3::exceptions::PyRuntimeError;
use pyo3::prelude::*;
use pyo3::types::PyAny;
use tokio::sync::mpsc;

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

/// Send a message using a separate thread (to avoid nested runtime issues)
fn send_message_in_thread(
    db_path: String,
    recipient: String,
    message: String,
) -> Result<(), String> {
    let handle = std::thread::spawn(move || {
        run_local_async(async move {
            let store = SqliteStore::open(&db_path, OnNewIdentity::Trust)
                .await
                .map_err(|e| format!("Failed to open store: {e}"))?;

            let mut manager = Manager::load_registered(store)
                .await
                .map_err(|e| format!("Not registered: {e}"))?;

            let recipient_uuid: Uuid = recipient
                .parse()
                .map_err(|e| format!("Invalid UUID: {e}"))?;

            let service_id = ServiceId::Aci(recipient_uuid.into());

            let timestamp = std::time::SystemTime::now()
                .duration_since(UNIX_EPOCH)
                .expect("Time went backwards")
                .as_millis() as u64;

            let data_message = DataMessage {
                body: Some(message),
                timestamp: Some(timestamp),
                ..Default::default()
            };
            let content_body = ContentBody::DataMessage(data_message);

            manager
                .send_message(service_id, content_body, timestamp)
                .await
                .map_err(|e| format!("Failed to send: {e}"))?;

            Ok(())
        })
    });

    handle.join().map_err(|_| "Thread panicked".to_string())?
}

/// Outgoing message to be sent
enum OutgoingMessage {
    Send {
        recipient: String,
        message: String,
        group_id: Option<String>,
    },
    Stop,
}

/// Signal client for sending and receiving messages
#[pyclass]
pub struct SignalClient {
    db_path: String,
    /// Channel sender for queuing messages to send (active during receive loop)
    send_tx: Arc<Mutex<Option<mpsc::UnboundedSender<OutgoingMessage>>>>,
    /// Stop flag that can be set from any thread
    stop_flag: Arc<AtomicBool>,
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

        Ok(Self {
            db_path,
            send_tx: Arc::new(Mutex::new(None)),
            stop_flag: Arc::new(AtomicBool::new(false)),
        })
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
    ///
    /// If called from within a receive callback, uses the shared connection.
    /// Otherwise, creates a new connection (slower but works outside receive loop).
    fn send_message_sync(&self, recipient: &str, message: &str) -> PyResult<()> {
        // Try to use the queue if receive loop is active
        {
            let tx_guard = self.send_tx.lock().unwrap();
            if let Some(ref tx) = *tx_guard {
                tx.send(OutgoingMessage::Send {
                    recipient: recipient.to_string(),
                    message: message.to_string(),
                    group_id: None,
                })
                .map_err(|_| PyRuntimeError::new_err("Failed to queue message"))?;
                return Ok(());
            }
        }

        // Fallback: use separate thread/connection (for use outside receive loop)
        let db_path = self.db_path.clone();
        let recipient = recipient.to_string();
        let message = message.to_string();

        send_message_in_thread(db_path, recipient, message).map_err(|e| PyRuntimeError::new_err(e))
    }

    /// Send a message to a group (sync, blocking)
    ///
    /// Args:
    ///     group_id: Base64-encoded group master key
    ///     message: Text message to send
    ///
    /// If called from within a receive callback, uses the shared connection.
    fn send_group_message_sync(
        &self,
        py: Python<'_>,
        group_id: &str,
        message: &str,
    ) -> PyResult<()> {
        // Try to use the queue if receive loop is active
        {
            let tx_guard = self.send_tx.lock().unwrap();
            if let Some(ref tx) = *tx_guard {
                tx.send(OutgoingMessage::Send {
                    recipient: String::new(),
                    message: message.to_string(),
                    group_id: Some(group_id.to_string()),
                })
                .map_err(|_| PyRuntimeError::new_err("Failed to queue message"))?;
                return Ok(());
            }
        }

        // Fallback: use separate connection
        let db_path = self.db_path.clone();
        let group_id_str = group_id.to_string();
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
                    .decode(&group_id_str)
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
    /// Messages sent via send_message_sync during the callback will use
    /// the same connection (more efficient, no reconnection issues).
    ///
    /// Responds to SIGINT (Ctrl+C) and SIGTERM for clean shutdown.
    fn receive_messages_sync(&self, py: Python<'_>, callback: Py<PyAny>) -> PyResult<()> {
        let db_path = self.db_path.clone();
        let send_tx = self.send_tx.clone();

        // Channel to signal stop from main thread to background thread
        let (stop_tx, stop_rx) = std::sync::mpsc::channel::<()>();

        // Channel to send received messages from background thread to main thread
        // (so Python callbacks are called from main thread, not background thread)
        let (msg_tx, msg_rx) = std::sync::mpsc::channel::<Message>();

        // Channel to signal completion from background thread
        let (done_tx, done_rx) = std::sync::mpsc::channel::<Result<(), String>>();

        // Run the receive loop in a background thread
        // This thread does NOT call Python - it just sends messages via channel
        std::thread::spawn(move || {
            let result = run_local_async(async move {
                let store = SqliteStore::open(&db_path, OnNewIdentity::Trust)
                    .await
                    .map_err(|e| format!("Failed to open store: {e}"))?;

                let mut manager = Manager::load_registered(store)
                    .await
                    .map_err(|e| format!("Not registered: {e}"))?;

                // Create channel for outgoing messages
                let (tx, mut rx) = mpsc::unbounded_channel::<OutgoingMessage>();

                // Store sender so send_message_sync can use it
                {
                    let mut tx_guard = send_tx.lock().unwrap();
                    *tx_guard = Some(tx.clone());
                }

                // Thread to monitor stop_rx and send Stop to channel
                let tx_stop = tx.clone();
                std::thread::spawn(move || {
                    if stop_rx.recv().is_ok() {
                        let _ = tx_stop.send(OutgoingMessage::Stop);
                    }
                });

                // Receive messages
                let messages = manager
                    .receive_messages()
                    .await
                    .map_err(|e| format!("Failed to receive: {e}"))?;
                pin_mut!(messages);
                tracing::debug!("Background: receive stream ready");

                // Process incoming messages using select! to handle stop signals
                loop {
                    tokio::select! {
                        biased;  // Check commands first

                        cmd = rx.recv() => {
                            match cmd {
                                Some(OutgoingMessage::Stop) => {
                                    tracing::debug!("Background: Stop signal received");
                                    break;
                                }
                                Some(OutgoingMessage::Send { recipient, message, group_id }) => {
                                    let timestamp = std::time::SystemTime::now()
                                        .duration_since(UNIX_EPOCH)
                                        .expect("Time went backwards")
                                        .as_millis() as u64;

                                    let data_message = DataMessage {
                                        body: Some(message),
                                        timestamp: Some(timestamp),
                                        ..Default::default()
                                    };
                                    let content_body = ContentBody::DataMessage(data_message);

                                    if let Some(gid) = group_id {
                                        if let Ok(master_key_bytes) = BASE64.decode(&gid) {
                                            if let Ok(master_key) = master_key_bytes.try_into() {
                                                let master_key: [u8; 32] = master_key;
                                                if let Err(e) = manager
                                                    .send_message_to_group(&master_key, content_body, timestamp)
                                                    .await
                                                {
                                                    tracing::error!("Group message error: {e}");
                                                }
                                            }
                                        }
                                    } else if let Ok(recipient_uuid) = recipient.parse::<Uuid>() {
                                        let service_id = ServiceId::Aci(recipient_uuid.into());
                                        if let Err(e) = manager
                                            .send_message(service_id, content_body, timestamp)
                                            .await
                                        {
                                            tracing::error!("Message error: {e}");
                                        }
                                    }
                                }
                                None => {
                                    // Channel closed, exit
                                    tracing::debug!("Background: command channel closed");
                                    break;
                                }
                            }
                        }

                        received = messages.next() => {
                            match received {
                                Some(Received::QueueEmpty) => {
                                    let msg = Message {
                                        sender: String::new(),
                                        body: None,
                                        timestamp: 0,
                                        group_id: None,
                                        is_read_receipt: false,
                                        is_typing_indicator: false,
                                        is_queue_empty: true,
                                    };
                                    if msg_tx.send(msg).is_err() {
                                        break;
                                    }
                                }
                                Some(Received::Contacts) => {
                                    // Skip contacts sync
                                }
                                Some(Received::Content(content)) => {
                                    if let Some(msg) = content_to_message(&content) {
                                        if msg_tx.send(msg).is_err() {
                                            break;
                                        }
                                    }
                                }
                                None => {
                                    // Stream ended
                                    tracing::info!("Background: message stream ended");
                                    break;
                                }
                            }
                        }
                    }
                }

                // Clean up: remove sender so send_message_sync falls back to thread
                {
                    let mut tx_guard = send_tx.lock().unwrap();
                    *tx_guard = None;
                }

                Ok(())
            });
            let _ = done_tx.send(result);
        });

        // Set up signal handler using signal-hook
        // This catches SIGINT directly in Rust, bypassing Python's signal handling issues
        let signal_received = Arc::new(AtomicBool::new(false));
        let _ = signal_flag::register(SIGINT, Arc::clone(&signal_received));

        // Main thread: handle Python callbacks and signal checking
        loop {
            // Check for SIGINT via signal-hook
            if signal_received.load(Ordering::Relaxed) {
                // Tell the background thread to stop
                let _ = stop_tx.send(());

                // Wait for background thread to finish (with short timeout)
                for _ in 0..20 {
                    // 2 second timeout
                    if let Ok(result) = done_rx.try_recv() {
                        return match result {
                            Ok(()) => Err(pyo3::exceptions::PyKeyboardInterrupt::new_err(
                                "Interrupted",
                            )),
                            Err(e) => Err(PyRuntimeError::new_err(e)),
                        };
                    }
                    std::thread::sleep(std::time::Duration::from_millis(100));
                }
                // Timeout - return anyway, process will exit
                return Err(pyo3::exceptions::PyKeyboardInterrupt::new_err(
                    "Interrupted",
                ));
            }

            // Also check Python signals (in case other signals come through)
            if let Err(e) = py.check_signals() {
                let _ = stop_tx.send(());
                // Wait for background thread with timeout
                for _ in 0..50 {
                    if done_rx.try_recv().is_ok() {
                        break;
                    }
                    std::thread::sleep(std::time::Duration::from_millis(100));
                }
                return Err(e);
            }

            // Check for received messages and call the Python callback
            match msg_rx.try_recv() {
                Ok(msg) => {
                    // Call the Python callback
                    let should_continue = callback
                        .call1(py, (msg,))
                        .and_then(|r| r.extract::<bool>(py))
                        .unwrap_or(true);

                    if !should_continue {
                        // Callback returned False, stop receiving
                        let _ = stop_tx.send(());
                        return Ok(());
                    }
                }
                Err(std::sync::mpsc::TryRecvError::Empty) => {
                    // No messages, continue
                }
                Err(std::sync::mpsc::TryRecvError::Disconnected) => {
                    // Channel closed, background thread is done
                }
            }

            // Check if background thread is done
            match done_rx.try_recv() {
                Ok(Ok(())) => return Ok(()),
                Ok(Err(e)) => return Err(PyRuntimeError::new_err(e)),
                Err(std::sync::mpsc::TryRecvError::Empty) => {
                    // Not done yet - release GIL while sleeping
                    py.detach(|| {
                        std::thread::sleep(std::time::Duration::from_millis(10));
                    });
                }
                Err(std::sync::mpsc::TryRecvError::Disconnected) => {
                    return Err(PyRuntimeError::new_err(
                        "Background thread terminated unexpectedly",
                    ));
                }
            }
        }
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
                        members: group
                            .members
                            .iter()
                            .map(|m| m.aci.service_id_string())
                            .collect(),
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
    fn find_contact_by_phone_sync(&self, py: Python<'_>, phone: &str) -> PyResult<Option<Contact>> {
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
                        let normalized_search: String = phone
                            .chars()
                            .filter(|c| c.is_ascii_digit() || *c == '+')
                            .collect();
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
    fn find_contacts_by_name_sync(&self, py: Python<'_>, name: &str) -> PyResult<Vec<Contact>> {
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

    /// Stop the receive loop
    ///
    /// Call this to cleanly stop receive_messages_sync.
    /// This is thread-safe and can be called from signal handlers.
    fn stop(&self) -> PyResult<()> {
        // Set the stop flag (thread-safe)
        self.stop_flag.store(true, Ordering::SeqCst);

        // Also try to send via channel if available
        let tx_guard = self.send_tx.lock().unwrap();
        if let Some(ref tx) = *tx_guard {
            let _ = tx.send(OutgoingMessage::Stop);
        }
        Ok(())
    }

    /// Reset the stop flag (call before starting receive loop again)
    fn reset_stop(&self) -> PyResult<()> {
        self.stop_flag.store(false, Ordering::SeqCst);
        Ok(())
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
