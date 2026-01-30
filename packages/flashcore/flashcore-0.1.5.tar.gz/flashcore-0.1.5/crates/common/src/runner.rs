// -------------------------------------------------------------------------------------------------
//  Copyright (C) 2015-2026 Nautech Systems Pty Ltd. All rights reserved.
//  https://nautechsystems.io
//
//  Licensed under the GNU Lesser General Public License Version 3.0 (the "License");
//  You may not use this file except in compliance with the License.
//  You may obtain a copy of the License at https://www.gnu.org/licenses/lgpl-3.0.en.html
//
//  Unless required by applicable law or agreed to in writing, software
//  distributed under the License is distributed on an "AS IS" BASIS,
//  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
//  See the License for the specific language governing permissions and
//  limitations under the License.
// -------------------------------------------------------------------------------------------------

//! Minimal time event sender registry used by clocks.

use std::{cell::OnceCell, fmt::Debug, sync::Arc};

use crate::timer::TimeEventHandler;

/// Trait for time event sending that can be implemented for both sync and async runners.
pub trait TimeEventSender: Debug + Send + Sync {
    /// Sends a time event handler.
    fn send(&self, handler: TimeEventHandler);
}

/// Gets the global time event sender.
///
/// # Panics
///
/// Panics if the sender is uninitialized.
#[must_use]
pub fn get_time_event_sender() -> Arc<dyn TimeEventSender> {
    TIME_EVENT_SENDER.with(|sender| {
        sender
            .get()
            .expect("Time event sender should be initialized by runner")
            .clone()
    })
}

/// Attempts to get the global time event sender without panicking.
///
/// Returns `None` if the sender is not initialized (e.g., in test environments).
#[must_use]
pub fn try_get_time_event_sender() -> Option<Arc<dyn TimeEventSender>> {
    TIME_EVENT_SENDER.with(|sender| sender.get().cloned())
}

/// Sets the global time event sender.
///
/// Can only be called once per thread.
///
/// # Panics
///
/// Panics if a sender has already been set.
pub fn set_time_event_sender(sender: Arc<dyn TimeEventSender>) {
    TIME_EVENT_SENDER.with(|s| {
        assert!(
            s.set(sender).is_ok(),
            "Time event sender can only be set once"
        );
    });
}

thread_local! {
    static TIME_EVENT_SENDER: OnceCell<Arc<dyn TimeEventSender>> = const { OnceCell::new() };
}
