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

use std::{
    collections::{HashMap, HashSet},
    hash::{Hash, Hasher},
    str::FromStr,
};

use indexmap::IndexMap;
use nautilus_common::{
    clock::Clock,
    clock::TestClock as CoreTestClock,
    live::clock::LiveClock as CoreLiveClock,
    timer::{TimeEvent as CoreTimeEvent, TimeEventCallback},
};
use nautilus_core::python::IntoPyObjectNautilusExt;
use nautilus_core::UUID4 as CoreUUID4;
use nautilus_cryptography::signing::{ed25519_signature, hmac_signature, rsa_signature};
use nautilus_model::identifiers::TraderId as CoreTraderId;
use pyo3::{
    basic::CompareOp,
    exceptions::PyValueError,
    prelude::*,
    types::{PyBytes, PyCapsule, PyFloat, PyInt, PySet, PyString, PyTuple},
};
use ustr::Ustr;

fn to_value_error(err: impl std::fmt::Display) -> PyErr {
    PyValueError::new_err(err.to_string())
}

fn is_matching(topic: &[u8], pattern: &[u8]) -> bool {
    if topic.len() == pattern.len() && !pattern.contains(&b'*') && !pattern.contains(&b'?') {
        return topic == pattern;
    }

    let mut i = 0;
    let mut j = 0;
    let mut star_idx: Option<usize> = None;
    let mut match_idx = 0;

    while i < topic.len() {
        if j < pattern.len() && (pattern[j] == b'?' || pattern[j] == topic[i]) {
            i += 1;
            j += 1;
        } else if j < pattern.len() && pattern[j] == b'*' {
            star_idx = Some(j);
            match_idx = i;
            j += 1;
        } else if let Some(si) = star_idx {
            j = si + 1;
            match_idx += 1;
            i = match_idx;
        } else {
            return false;
        }
    }

    while j < pattern.len() && pattern[j] == b'*' {
        j += 1;
    }

    j == pattern.len()
}

fn handler_repr(py: Python<'_>, handler: &Py<PyAny>) -> String {
    handler
        .bind(py)
        .repr()
        .and_then(|repr| repr.to_str().map(|text| text.to_string()))
        .unwrap_or_else(|_| format!("handler_ptr={}", handler.as_ptr() as usize))
}

fn datetime_to_ns(_py: Python<'_>, value: &Bound<'_, PyAny>) -> PyResult<u64> {
    let timestamp = value.call_method0("timestamp")?.extract::<f64>()?;
    if !timestamp.is_finite() || timestamp < 0.0 {
        return Err(PyValueError::new_err("datetime must be a valid, non-negative timestamp"));
    }
    Ok((timestamp * 1_000_000_000.0).round() as u64)
}

fn timedelta_to_ns(_py: Python<'_>, value: &Bound<'_, PyAny>) -> PyResult<u64> {
    let seconds = value.call_method0("total_seconds")?.extract::<f64>()?;
    if !seconds.is_finite() || seconds < 0.0 {
        return Err(PyValueError::new_err("timedelta must be a valid, non-negative duration"));
    }
    Ok((seconds * 1_000_000_000.0).round() as u64)
}

#[pyclass(module = "flashcore")]
struct PyTimeEventHandler {
    callback: Py<PyAny>,
}

#[pymethods]
impl PyTimeEventHandler {
    #[new]
    fn py_new(callback: Py<PyAny>) -> Self {
        Self { callback }
    }

    fn __call__(&self, py: Python<'_>, event: &Bound<'_, PyAny>) -> PyResult<()> {
        // Check if the event is already a wrapped TimeEvent (from flashcore module)
        if event.extract::<TimeEvent>().is_ok() {
            self.callback.call1(py, (event,))?;
            return Ok(());
        }

        // Try to extract as CoreTimeEvent and wrap it
        if let Ok(core_event) = event.extract::<CoreTimeEvent>() {
            let wrapped = Py::new(py, TimeEvent(core_event))?;
            self.callback.call1(py, (wrapped,))?;
            return Ok(());
        }

        // Check for capsule (legacy path)
        if let Ok(capsule) = event.cast::<PyCapsule>() {
            let _ = capsule; // Capsule contents are opaque; create a minimal wrapper event.
            let fallback = CoreTimeEvent::new(Ustr::from("time_event"), CoreUUID4::new(), 0.into(), 0.into());
            let wrapped = Py::new(py, TimeEvent(fallback))?;
            self.callback.call1(py, (wrapped,))?;
            return Ok(());
        }

        // Default: pass event through unchanged
        self.callback.call1(py, (event,))?;
        Ok(())
    }
}

fn wrap_time_event_callback(py: Python<'_>, callback: Py<PyAny>) -> PyResult<Py<PyAny>> {
    let wrapper = Py::new(py, PyTimeEventHandler { callback })?;
    Ok(wrapper.into())
}

#[pyclass(module = "flashcore")]
#[derive(Clone, Copy, Debug, Hash, PartialEq, Eq)]
pub struct UUID4(CoreUUID4);

#[pymethods]
impl UUID4 {
    #[new]
    fn py_new() -> Self {
        Self(CoreUUID4::new())
    }

    fn __getstate__(&self) -> String {
        self.0.to_string()
    }

    fn __setstate__(&mut self, state: &str) -> PyResult<()> {
        self.0 = CoreUUID4::from_str(state).map_err(to_value_error)?;
        Ok(())
    }

    fn __richcmp__(&self, other: &Self, op: CompareOp, py: Python<'_>) -> Py<PyAny> {
        match op {
            CompareOp::Eq => (self.0 == other.0).into_py_any_unwrap(py),
            CompareOp::Ne => (self.0 != other.0).into_py_any_unwrap(py),
            _ => py.NotImplemented().into_py_any_unwrap(py),
        }
    }

    fn __hash__(&self) -> u64 {
        let mut h = std::collections::hash_map::DefaultHasher::new();
        self.0.hash(&mut h);
        h.finish()
    }

    fn __str__(&self) -> String {
        self.0.to_string()
    }

    fn __repr__(&self) -> String {
        format!("UUID4('{}')", self.0)
    }

    #[getter]
    fn value(&self) -> String {
        self.0.to_string()
    }

    #[staticmethod]
    fn from_str(value: &str) -> PyResult<Self> {
        Ok(Self(CoreUUID4::from_str(value).map_err(to_value_error)?))
    }
}

#[pyclass(module = "flashcore")]
#[derive(Clone, Copy, Debug, Hash, PartialEq, Eq, PartialOrd, Ord)]
pub struct TraderId(CoreTraderId);

#[pymethods]
impl TraderId {
    #[new]
    fn py_new(value: &str) -> PyResult<Self> {
        Ok(Self(CoreTraderId::new_checked(value).map_err(to_value_error)?))
    }

    fn __getstate__(&self) -> String {
        self.0.to_string()
    }

    fn __setstate__(&mut self, state: &str) -> PyResult<()> {
        self.0 = CoreTraderId::new_checked(state).map_err(to_value_error)?;
        Ok(())
    }

    fn __richcmp__(&self, other: &Self, op: CompareOp, py: Python<'_>) -> Py<PyAny> {
        match op {
            CompareOp::Eq => (self.0 == other.0).into_py_any_unwrap(py),
            CompareOp::Ne => (self.0 != other.0).into_py_any_unwrap(py),
            CompareOp::Lt => (self.0 < other.0).into_py_any_unwrap(py),
            CompareOp::Le => (self.0 <= other.0).into_py_any_unwrap(py),
            CompareOp::Gt => (self.0 > other.0).into_py_any_unwrap(py),
            CompareOp::Ge => (self.0 >= other.0).into_py_any_unwrap(py),
        }
    }

    fn __hash__(&self) -> u64 {
        let mut h = std::collections::hash_map::DefaultHasher::new();
        self.0.hash(&mut h);
        h.finish()
    }

    fn __str__(&self) -> String {
        self.0.to_string()
    }

    fn __repr__(&self) -> String {
        format!("TraderId('{}')", self.0)
    }

    #[getter]
    fn value(&self) -> String {
        self.0.to_string()
    }

    fn get_tag(&self) -> String {
        self.0.get_tag().to_string()
    }
}

#[pyclass(module = "flashcore")]
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct TimeEvent(CoreTimeEvent);

#[pymethods]
impl TimeEvent {
    #[new]
    fn py_new(name: &str, event_id: UUID4, ts_event: u64, ts_init: u64) -> Self {
        Self(CoreTimeEvent::new(
            Ustr::from(name),
            event_id.0,
            ts_event.into(),
            ts_init.into(),
        ))
    }

    fn __getstate__(&self, py: Python<'_>) -> PyResult<Py<PyAny>> {
        Ok((
            self.0.name.to_string(),
            self.0.event_id.to_string(),
            self.0.ts_event.as_u64(),
            self.0.ts_init.as_u64(),
        )
        .into_py_any_unwrap(py))
    }

    fn __setstate__(&mut self, state: &Bound<'_, PyAny>) -> PyResult<()> {
        let py_tuple: &Bound<'_, PyTuple> = state.cast::<PyTuple>()?;
        let name = py_tuple.get_item(0)?.extract::<String>()?;
        let event_id = py_tuple.get_item(1)?.extract::<String>()?;
        let ts_event = py_tuple.get_item(2)?.extract::<u64>()?;
        let ts_init = py_tuple.get_item(3)?.extract::<u64>()?;

        self.0 = CoreTimeEvent::new(
            Ustr::from(name.as_str()),
            CoreUUID4::from_str(&event_id).map_err(to_value_error)?,
            ts_event.into(),
            ts_init.into(),
        );
        Ok(())
    }

    fn __richcmp__(&self, other: &Self, op: CompareOp, py: Python<'_>) -> Py<PyAny> {
        match op {
            CompareOp::Eq => (self.0.event_id == other.0.event_id).into_py_any_unwrap(py),
            CompareOp::Ne => (self.0.event_id != other.0.event_id).into_py_any_unwrap(py),
            _ => py.NotImplemented().into_py_any_unwrap(py),
        }
    }

    fn __hash__(&self) -> u64 {
        let mut h = std::collections::hash_map::DefaultHasher::new();
        self.0.event_id.hash(&mut h);
        h.finish()
    }

    fn __str__(&self) -> String {
        self.0.name.to_string()
    }

    fn __repr__(&self) -> String {
        self.0.to_string()
    }

    #[getter]
    fn name(&self) -> String {
        self.0.name.to_string()
    }

    #[getter]
    fn id(&self) -> UUID4 {
        UUID4(self.0.event_id)
    }

    #[getter]
    fn ts_event(&self) -> u64 {
        self.0.ts_event.as_u64()
    }

    #[getter]
    fn ts_init(&self) -> u64 {
        self.0.ts_init.as_u64()
    }
}

#[pyclass(module = "flashcore", unsendable)]
#[derive(Debug)]
pub struct LiveClock {
    inner: CoreLiveClock,
}

#[pymethods]
impl LiveClock {
    #[new]
    fn py_new() -> Self {
        Self {
            inner: CoreLiveClock::default(),
        }
    }

    #[getter]
    fn timer_names(&self) -> Vec<String> {
        self.inner
            .timer_names()
            .into_iter()
            .map(|name| name.to_string())
            .collect()
    }

    #[getter]
    fn timer_count(&self) -> usize {
        self.inner.timer_count()
    }

    fn timestamp(&self) -> f64 {
        self.inner.timestamp()
    }

    fn timestamp_ms(&self) -> u64 {
        self.inner.timestamp_ms()
    }

    fn timestamp_us(&self) -> u64 {
        self.inner.timestamp_us()
    }

    fn timestamp_ns(&self) -> u64 {
        self.inner.timestamp_ns().as_u64()
    }

    fn utc_now(&self, py: Python<'_>) -> PyResult<Py<PyAny>> {
        let datetime_module = py.import("datetime")?;
        let datetime = datetime_module.getattr("datetime")?;
        let utc = datetime_module.getattr("timezone")?.getattr("utc")?;
        let value = datetime.call_method1("fromtimestamp", (self.timestamp(), utc))?;
        Ok(value.unbind())
    }

    fn local_now(&self, py: Python<'_>, tz: Py<PyAny>) -> PyResult<Py<PyAny>> {
        let datetime = py.import("datetime")?.getattr("datetime")?;
        let value = datetime.call_method1("fromtimestamp", (self.timestamp(), tz))?;
        Ok(value.unbind())
    }

    fn register_default_handler(&mut self, py: Python<'_>, callback: Py<PyAny>) -> PyResult<()> {
        if !callback.bind(py).is_callable() {
            return Err(PyValueError::new_err("callback must be callable"));
        }
        let wrapped = wrap_time_event_callback(py, callback)?;
        self.inner
            .register_default_handler(TimeEventCallback::from(wrapped));
        Ok(())
    }

    #[pyo3(signature = (name, alert_time_ns, callback=None, allow_past=true))]
    fn set_time_alert_ns(
        &mut self,
        py: Python<'_>,
        name: &str,
        alert_time_ns: u64,
        callback: Option<Py<PyAny>>,
        allow_past: bool,
    ) -> PyResult<()> {
        if self.timer_names().iter().any(|existing| existing == name) {
            return Err(PyValueError::new_err("timer name already exists"));
        }
        if !allow_past {
            let ts_now = self.timestamp_ns();
            if alert_time_ns < ts_now {
                return Err(PyValueError::new_err(format!(
                    "Timer '{name}' alert time was in the past"
                )));
            }
        }

        let callback = match callback {
            Some(value) => Some(TimeEventCallback::from(wrap_time_event_callback(py, value)?)),
            None => None,
        };

        self.inner
            .set_time_alert_ns(name, alert_time_ns.into(), callback, Some(allow_past))
            .map_err(to_value_error)
    }

    #[pyo3(signature = (name, alert_time, callback=None, allow_past=true))]
    fn set_time_alert(
        &mut self,
        py: Python<'_>,
        name: &str,
        alert_time: &Bound<'_, PyAny>,
        callback: Option<Py<PyAny>>,
        allow_past: bool,
    ) -> PyResult<()> {
        let alert_time_ns = datetime_to_ns(py, alert_time)?;
        self.set_time_alert_ns(py, name, alert_time_ns, callback, allow_past)
    }

    #[allow(clippy::too_many_arguments)]
    #[pyo3(
        signature = (name, interval_ns, start_time_ns, stop_time_ns, callback=None, allow_past=true, fire_immediately=false)
    )]
    fn set_timer_ns(
        &mut self,
        py: Python<'_>,
        name: &str,
        interval_ns: u64,
        start_time_ns: u64,
        stop_time_ns: u64,
        callback: Option<Py<PyAny>>,
        allow_past: bool,
        fire_immediately: bool,
    ) -> PyResult<()> {
        if self.timer_names().iter().any(|existing| existing == name) {
            return Err(PyValueError::new_err("timer name already exists"));
        }
        if interval_ns == 0 {
            return Err(PyValueError::new_err("Interval must be positive"));
        }

        if !allow_past && start_time_ns != 0 {
            let ts_now = self.timestamp_ns();
            let next_event_time = if fire_immediately {
                start_time_ns
            } else {
                start_time_ns.saturating_add(interval_ns)
            };
            if next_event_time < ts_now {
                return Err(PyValueError::new_err(format!(
                    "Timer '{name}' next event time would be in the past"
                )));
            }
        }

        let start_time_ns = if start_time_ns == 0 {
            None
        } else {
            Some(start_time_ns.into())
        };
        let stop_time_ns = if stop_time_ns == 0 {
            None
        } else {
            Some(stop_time_ns.into())
        };

        let callback = match callback {
            Some(value) => Some(TimeEventCallback::from(wrap_time_event_callback(py, value)?)),
            None => None,
        };

        self.inner
            .set_timer_ns(
                name,
                interval_ns,
                start_time_ns,
                stop_time_ns,
                callback,
                Some(allow_past),
                Some(fire_immediately),
            )
            .map_err(to_value_error)
    }

    #[allow(clippy::too_many_arguments)]
    #[pyo3(
        signature = (name, interval, start_time=None, stop_time=None, callback=None, allow_past=true, fire_immediately=false)
    )]
    fn set_timer(
        &mut self,
        py: Python<'_>,
        name: &str,
        interval: &Bound<'_, PyAny>,
        start_time: Option<&Bound<'_, PyAny>>,
        stop_time: Option<&Bound<'_, PyAny>>,
        callback: Option<Py<PyAny>>,
        allow_past: bool,
        fire_immediately: bool,
    ) -> PyResult<()> {
        let interval_ns = timedelta_to_ns(py, interval)?;
        let start_time_ns = match start_time {
            Some(value) => datetime_to_ns(py, value)?,
            None => 0,
        };
        let stop_time_ns = match stop_time {
            Some(value) => datetime_to_ns(py, value)?,
            None => 0,
        };

        self.set_timer_ns(
            py,
            name,
            interval_ns,
            start_time_ns,
            stop_time_ns,
            callback,
            allow_past,
            fire_immediately,
        )
    }

    fn next_time_ns(&self, name: &str) -> u64 {
        self.inner
            .next_time_ns(name)
            .map(|t| t.as_u64())
            .unwrap_or_default()
    }

    fn cancel_timer(&mut self, name: &str) {
        self.inner.cancel_timer(name);
    }

    fn cancel_timers(&mut self) {
        self.inner.cancel_timers();
    }
}

#[pyclass(module = "flashcore", unsendable)]
#[derive(Debug)]
pub struct TestClock {
    inner: CoreTestClock,
}

#[pymethods]
impl TestClock {
    #[new]
    fn py_new() -> Self {
        Self {
            inner: CoreTestClock::default(),
        }
    }

    #[getter]
    fn timer_names(&self) -> Vec<String> {
        self.inner
            .timer_names()
            .into_iter()
            .map(|name| name.to_string())
            .collect()
    }

    #[getter]
    fn timer_count(&self) -> usize {
        self.inner.timer_count()
    }

    fn timestamp(&self) -> f64 {
        self.inner.timestamp()
    }

    fn timestamp_ms(&self) -> u64 {
        self.inner.timestamp_ms()
    }

    fn timestamp_us(&self) -> u64 {
        self.inner.timestamp_us()
    }

    fn timestamp_ns(&self) -> u64 {
        self.inner.timestamp_ns().as_u64()
    }

    #[pyo3(signature = (name, alert_time, callback=None, allow_past=true))]
    fn set_time_alert(
        &mut self,
        py: Python<'_>,
        name: &str,
        alert_time: &Bound<'_, PyAny>,
        callback: Option<Py<PyAny>>,
        allow_past: bool,
    ) -> PyResult<()> {
        let alert_time_ns = datetime_to_ns(py, alert_time)?;
        self.set_time_alert_ns(py, name, alert_time_ns, callback, allow_past)
    }

    #[allow(clippy::too_many_arguments)]
    #[pyo3(
        signature = (name, interval, start_time=None, stop_time=None, callback=None, allow_past=true, fire_immediately=false)
    )]
    fn set_timer(
        &mut self,
        py: Python<'_>,
        name: &str,
        interval: &Bound<'_, PyAny>,
        start_time: Option<&Bound<'_, PyAny>>,
        stop_time: Option<&Bound<'_, PyAny>>,
        callback: Option<Py<PyAny>>,
        allow_past: bool,
        fire_immediately: bool,
    ) -> PyResult<()> {
        let interval_ns = timedelta_to_ns(py, interval)?;
        let start_time_ns = match start_time {
            Some(value) => datetime_to_ns(py, value)?,
            None => 0,
        };
        let stop_time_ns = match stop_time {
            Some(value) => datetime_to_ns(py, value)?,
            None => 0,
        };

        self.set_timer_ns(
            py,
            name,
            interval_ns,
            start_time_ns,
            stop_time_ns,
            callback,
            allow_past,
            fire_immediately,
        )
    }

    fn utc_now(&self, py: Python<'_>) -> PyResult<Py<PyAny>> {
        let datetime_module = py.import("datetime")?;
        let datetime = datetime_module.getattr("datetime")?;
        let utc = datetime_module.getattr("timezone")?.getattr("utc")?;
        let value = datetime.call_method1("fromtimestamp", (self.timestamp(), utc))?;
        Ok(value.unbind())
    }

    fn local_now(&self, py: Python<'_>, tz: Py<PyAny>) -> PyResult<Py<PyAny>> {
        let datetime = py.import("datetime")?.getattr("datetime")?;
        let value = datetime.call_method1("fromtimestamp", (self.timestamp(), tz))?;
        Ok(value.unbind())
    }

    fn register_default_handler(&mut self, py: Python<'_>, callback: Py<PyAny>) -> PyResult<()> {
        if !callback.bind(py).is_callable() {
            return Err(PyValueError::new_err("callback must be callable"));
        }
        let wrapped = wrap_time_event_callback(py, callback)?;
        self.inner
            .register_default_handler(TimeEventCallback::from(wrapped));
        Ok(())
    }

    #[pyo3(signature = (name, alert_time_ns, callback=None, allow_past=true))]
    fn set_time_alert_ns(
        &mut self,
        py: Python<'_>,
        name: &str,
        alert_time_ns: u64,
        callback: Option<Py<PyAny>>,
        allow_past: bool,
    ) -> PyResult<()> {
        if self.timer_names().iter().any(|existing| existing == name) {
            return Err(PyValueError::new_err("timer name already exists"));
        }
        if !allow_past {
            let ts_now = self.timestamp_ns();
            if alert_time_ns < ts_now {
                return Err(PyValueError::new_err(format!(
                    "Timer '{name}' alert time was in the past"
                )));
            }
        }

        let callback = match callback {
            Some(value) => Some(TimeEventCallback::from(wrap_time_event_callback(py, value)?)),
            None => None,
        };

        self.inner
            .set_time_alert_ns(name, alert_time_ns.into(), callback, Some(allow_past))
            .map_err(to_value_error)
    }

    #[allow(clippy::too_many_arguments)]
    #[pyo3(
        signature = (name, interval_ns, start_time_ns, stop_time_ns, callback=None, allow_past=true, fire_immediately=false)
    )]
    fn set_timer_ns(
        &mut self,
        py: Python<'_>,
        name: &str,
        interval_ns: u64,
        start_time_ns: u64,
        stop_time_ns: u64,
        callback: Option<Py<PyAny>>,
        allow_past: bool,
        fire_immediately: bool,
    ) -> PyResult<()> {
        if self.timer_names().iter().any(|existing| existing == name) {
            return Err(PyValueError::new_err("timer name already exists"));
        }
        if interval_ns == 0 {
            return Err(PyValueError::new_err("Interval must be positive"));
        }

        if !allow_past && start_time_ns != 0 {
            let ts_now = self.timestamp_ns();
            let next_event_time = if fire_immediately {
                start_time_ns
            } else {
                start_time_ns.saturating_add(interval_ns)
            };
            if next_event_time < ts_now {
                return Err(PyValueError::new_err(format!(
                    "Timer '{name}' next event time would be in the past"
                )));
            }
        }

        let start_time_ns = if start_time_ns == 0 {
            None
        } else {
            Some(start_time_ns.into())
        };
        let stop_time_ns = if stop_time_ns == 0 {
            None
        } else {
            Some(stop_time_ns.into())
        };

        let callback = match callback {
            Some(value) => Some(TimeEventCallback::from(wrap_time_event_callback(py, value)?)),
            None => None,
        };

        self.inner
            .set_timer_ns(
                name,
                interval_ns,
                start_time_ns,
                stop_time_ns,
                callback,
                Some(allow_past),
                Some(fire_immediately),
            )
            .map_err(to_value_error)
    }

    fn next_time_ns(&self, name: &str) -> u64 {
        self.inner
            .next_time_ns(name)
            .map(|t| t.as_u64())
            .unwrap_or_default()
    }

    fn cancel_timer(&mut self, name: &str) {
        self.inner.cancel_timer(name);
    }

    fn cancel_timers(&mut self) {
        self.inner.cancel_timers();
    }

    #[pyo3(signature = (to_time_ns, set_time=true))]
    fn advance_time(&mut self, to_time_ns: u64, set_time: bool) -> Vec<TimeEvent> {
        let events = self.inner.advance_time(to_time_ns.into(), set_time);
        let handlers = self.inner.match_handlers(events.clone());
        for handler in handlers {
            handler.run();
        }
        events.into_iter().map(TimeEvent).collect()
    }
}

#[derive(Clone, Debug)]
struct SubscriptionKey {
    topic: String,
    handler_ptr: usize,
}

impl PartialEq for SubscriptionKey {
    fn eq(&self, other: &Self) -> bool {
        self.topic == other.topic && self.handler_ptr == other.handler_ptr
    }
}

impl Eq for SubscriptionKey {}

impl Hash for SubscriptionKey {
    fn hash<H: Hasher>(&self, state: &mut H) {
        self.topic.hash(state);
        self.handler_ptr.hash(state);
    }
}

#[pyclass(module = "flashcore")]
#[derive(Debug)]
pub struct Subscription {
    #[pyo3(get)]
    topic: String,
    #[pyo3(get)]
    handler: Py<PyAny>,
    #[pyo3(get)]
    priority: i32,
}

impl Subscription {
    fn key(&self) -> SubscriptionKey {
        SubscriptionKey {
            topic: self.topic.clone(),
            handler_ptr: self.handler.as_ptr() as usize,
        }
    }

    fn handler_repr(&self, py: Python<'_>) -> String {
        self.handler
            .bind(py)
            .repr()
            .and_then(|repr| repr.to_str().map(|text| text.to_string()))
            .unwrap_or_else(|_| format!("handler_ptr={}", self.handler.as_ptr() as usize))
    }
}

impl Clone for Subscription {
    fn clone(&self) -> Self {
        Python::with_gil(|py| Self {
            topic: self.topic.clone(),
            handler: self.handler.clone_ref(py),
            priority: self.priority,
        })
    }
}

#[pymethods]
impl Subscription {
    #[new]
    #[pyo3(signature = (topic, handler, priority=0))]
    fn py_new(topic: &str, handler: Py<PyAny>, priority: i32) -> PyResult<Self> {
        if topic.is_empty() {
            return Err(PyValueError::new_err("topic must be a non-empty string"));
        }
        if priority < 0 {
            return Err(PyValueError::new_err("priority must be non-negative"));
        }
        Ok(Self {
            topic: topic.to_string(),
            handler,
            priority,
        })
    }

    fn __richcmp__(&self, other: &Self, op: CompareOp, py: Python<'_>) -> Py<PyAny> {
        match op {
            CompareOp::Eq => {
                let is_eq = self.topic == other.topic
                    && self.handler_repr(py) == other.handler_repr(py);
                is_eq.into_py_any_unwrap(py)
            }
            CompareOp::Ne => {
                let is_ne = self.topic != other.topic
                    || self.handler_repr(py) != other.handler_repr(py);
                is_ne.into_py_any_unwrap(py)
            }
            CompareOp::Lt => (self.priority < other.priority).into_py_any_unwrap(py),
            CompareOp::Le => (self.priority <= other.priority).into_py_any_unwrap(py),
            CompareOp::Gt => (self.priority > other.priority).into_py_any_unwrap(py),
            CompareOp::Ge => (self.priority >= other.priority).into_py_any_unwrap(py),
        }
    }

    fn __hash__(&self, py: Python<'_>) -> PyResult<isize> {
        let handler_repr = self.handler_repr(py);
        let tuple = (self.topic.clone(), handler_repr).into_py_any_unwrap(py);
        tuple.bind(py).hash()
    }

    fn __repr__(&self, py: Python<'_>) -> PyResult<String> {
        let handler_repr = self.handler_repr(py);
        Ok(format!(
            "Subscription(topic={}, handler={}, priority={})",
            self.topic, handler_repr, self.priority
        ))
    }
}

#[derive(Debug)]
struct SubscriptionEntry {
    subscription: Subscription,
    matches: Vec<String>,
}

#[pyclass(module = "flashcore", unsendable)]
#[derive(Debug)]
pub struct MessageBus {
    #[pyo3(get)]
    trader_id: TraderId,
    #[pyo3(get)]
    instance_id: UUID4,
    #[pyo3(get)]
    name: String,
    #[pyo3(get)]
    has_backing: bool,
    #[pyo3(get, set)]
    sent_count: u64,
    #[pyo3(get, set)]
    req_count: u64,
    #[pyo3(get, set)]
    res_count: u64,
    #[pyo3(get, set)]
    pub_count: u64,
    _clock: Py<PyAny>,
    #[pyo3(get, set)]
    serializer: Option<Py<PyAny>>,
    database: Option<Py<PyAny>>,
    endpoints: HashMap<String, Py<PyAny>>,
    patterns: HashMap<String, Vec<Subscription>>,
    subscriptions: IndexMap<SubscriptionKey, SubscriptionEntry>,
    correlation_index: HashMap<String, Py<PyAny>>,
    listeners: Vec<Py<PyAny>>,
    publishable_types: Vec<Py<PyAny>>,
    streaming_types: Vec<Py<PyAny>>,
    resolved: bool,
}

impl MessageBus {
    fn normalize_key(_py: Python<'_>, value: &Bound<'_, PyAny>) -> PyResult<String> {
        if let Ok(uuid) = value.extract::<UUID4>() {
            return Ok(uuid.value());
        }
        if let Ok(value_attr) = value.getattr("value") {
            if let Ok(value_str) = value_attr.extract::<String>() {
                return Ok(value_str);
            }
        }
        value.extract::<String>().or_else(|_| value.str()?.extract::<String>())
    }

    fn is_matching(topic: &str, pattern: &str) -> bool {
        is_matching(topic.as_bytes(), pattern.as_bytes())
    }

    fn insert_subscription_sorted(subs: &mut Vec<Subscription>, sub: Subscription) {
        subs.retain(|existing| existing.key() != sub.key());
        subs.push(sub);
        subs.sort_by(|a, b| b.priority.cmp(&a.priority));
    }

    fn resolve_subscriptions(&mut self, topic: &str) -> Vec<Subscription> {
        let mut subs_list: Vec<Subscription> = Vec::new();

        for entry in self.subscriptions.values() {
            if Self::is_matching(topic, entry.subscription.topic.as_str()) {
                subs_list.push(entry.subscription.clone());
            }
        }

        subs_list.sort_by(|a, b| b.priority.cmp(&a.priority));
        self.patterns
            .insert(topic.to_string(), subs_list.clone());

        for sub in &subs_list {
            if let Some(entry) = self.subscriptions.get_mut(&sub.key()) {
                if !entry.matches.contains(&topic.to_string()) {
                    entry.matches.push(topic.to_string());
                    entry.matches.sort();
                }
            }
        }

        subs_list
    }

    fn default_publishable_types(py: Python<'_>) -> Vec<Py<PyAny>> {
        vec![
            py.get_type::<PyString>().into_any().unbind(),
            py.get_type::<PyInt>().into_any().unbind(),
            py.get_type::<PyFloat>().into_any().unbind(),
            py.get_type::<PyBytes>().into_any().unbind(),
        ]
    }
}

#[pymethods]
impl MessageBus {
    #[new]
    #[pyo3(signature = (trader_id, clock, instance_id=None, name=None, serializer=None, database=None, config=None))]
    fn py_new(
        py: Python<'_>,
        trader_id: TraderId,
        clock: Py<PyAny>,
        instance_id: Option<UUID4>,
        name: Option<String>,
        serializer: Option<Py<PyAny>>,
        database: Option<Py<PyAny>>,
        config: Option<Py<PyAny>>,
    ) -> PyResult<Self> {
        let instance_id = instance_id.unwrap_or_else(UUID4::py_new);
        let name = name.unwrap_or_else(|| "MessageBus".to_string());
        let has_backing = database.is_some();

        let mut publishable_types = Self::default_publishable_types(py);

        if let Some(config) = config {
            if let Ok(types_filter) = config.bind(py).getattr("types_filter") {
                if !types_filter.is_none() {
                    if let Ok(iter) = types_filter.try_iter() {
                        let filter_ptrs: HashSet<usize> = iter
                            .filter_map(|item| item.ok())
                            .map(|item| item.as_ptr() as usize)
                            .collect();
                        publishable_types.retain(|ty| !filter_ptrs.contains(&(ty.as_ptr() as usize)));
                    }
                }
            }
        }

        Ok(Self {
            trader_id,
            instance_id,
            name,
            has_backing,
            sent_count: 0,
            req_count: 0,
            res_count: 0,
            pub_count: 0,
            _clock: clock,
            serializer,
            database,
            endpoints: HashMap::new(),
            patterns: HashMap::new(),
            subscriptions: IndexMap::new(),
            correlation_index: HashMap::new(),
            listeners: Vec::new(),
            publishable_types,
            streaming_types: Vec::new(),
            resolved: false,
        })
    }

    fn endpoints(&self) -> Vec<String> {
        self.endpoints.keys().cloned().collect()
    }

    fn topics(&self) -> Vec<String> {
        let mut topics: Vec<String> = self
            .subscriptions
            .values()
            .map(|entry| entry.subscription.topic.clone())
            .collect();
        topics.sort();
        topics.dedup();
        topics
    }

    #[pyo3(signature = (pattern=None))]
    fn subscriptions(&self, pattern: Option<&str>) -> Vec<Subscription> {
        let pattern = pattern.unwrap_or("*");
        self.subscriptions
            .values()
            .filter_map(|entry| {
                if Self::is_matching(entry.subscription.topic.as_str(), pattern) {
                    Some(entry.subscription.clone())
                } else {
                    None
                }
            })
            .collect()
    }

    fn streaming_types(&self, py: Python<'_>) -> PyResult<Py<PySet>> {
        let set = PySet::empty(py)?;
        for ty in &self.streaming_types {
            set.add(ty.bind(py))?;
        }
        Ok(set.into())
    }

    #[pyo3(signature = (pattern=None))]
    fn has_subscribers(&self, pattern: Option<&str>) -> bool {
        !self.subscriptions(pattern).is_empty()
    }

    fn is_subscribed(&self, topic: &str, handler: Py<PyAny>) -> bool {
        let key = SubscriptionKey {
            topic: topic.to_string(),
            handler_ptr: handler.as_ptr() as usize,
        };
        self.subscriptions.contains_key(&key)
    }

    fn is_pending_request(&self, py: Python<'_>, request_id: &Bound<'_, PyAny>) -> PyResult<bool> {
        let key = Self::normalize_key(py, request_id)?;
        Ok(self.correlation_index.contains_key(&key))
    }

    fn is_streaming_type(&self, cls: Py<PyAny>) -> bool {
        self.streaming_types
            .iter()
            .any(|existing| existing.as_ptr() == cls.as_ptr())
    }

    fn dispose(&mut self, py: Python<'_>) -> PyResult<()> {
        if let Some(database) = &self.database {
            if let Ok(close) = database.bind(py).getattr("close") {
                let _ = close.call0();
            }
        }
        Ok(())
    }

    fn register(&mut self, py: Python<'_>, endpoint: &str, handler: Py<PyAny>) -> PyResult<()> {
        if endpoint.is_empty() {
            return Err(PyValueError::new_err("endpoint must be a non-empty string"));
        }
        if !handler.bind(py).is_callable() {
            return Err(PyValueError::new_err("handler must be callable"));
        }
        if self.endpoints.contains_key(endpoint) {
            return Err(PyValueError::new_err("endpoint already registered"));
        }
        self.endpoints.insert(endpoint.to_string(), handler);
        Ok(())
    }

    fn deregister(&mut self, py: Python<'_>, endpoint: &str, handler: Py<PyAny>) -> PyResult<()> {
        if !handler.bind(py).is_callable() {
            return Err(PyValueError::new_err("handler must be callable"));
        }
        let existing = self
            .endpoints
            .get(endpoint)
            .ok_or_else(|| PyValueError::new_err("endpoint not registered"))?;
        if handler_repr(py, existing) != handler_repr(py, &handler) {
            return Err(PyValueError::new_err("handler not registered at endpoint"));
        }
        self.endpoints.remove(endpoint);
        Ok(())
    }

    fn add_streaming_type(&mut self, cls: Py<PyAny>) {
        if !self
            .streaming_types
            .iter()
            .any(|existing| existing.as_ptr() == cls.as_ptr())
        {
            self.streaming_types.push(cls);
        }
    }

    fn add_listener(&mut self, listener: Py<PyAny>) {
        self.listeners.push(listener);
    }

    fn send(&mut self, py: Python<'_>, endpoint: &str, msg: Py<PyAny>) {
        if let Some(handler) = self.endpoints.get(endpoint) {
            let _ = handler.bind(py).call1((msg,));
            self.sent_count += 1;
        } else {
            log::error!("Cannot send message: no endpoint registered at '{endpoint}'");
        }
    }

    fn request(&mut self, py: Python<'_>, endpoint: &str, request: Py<PyAny>) -> PyResult<()> {
        let request_ref = request.bind(py);
        let request_id = request_ref.getattr("id")?;
        let key = Self::normalize_key(py, &request_id)?;
        if self.correlation_index.contains_key(&key) {
            log::error!(
                "Cannot handle request: duplicate ID {key} found in correlation index"
            );
            return Ok(());
        }

        if let Ok(callback) = request_ref.getattr("callback") {
            if !callback.is_none() {
                self.correlation_index.insert(key, callback.unbind());
            }
        }

        if let Some(handler) = self.endpoints.get(endpoint) {
            let _ = handler.bind(py).call1((request,));
            self.req_count += 1;
        } else {
            log::error!("Cannot handle request: no endpoint registered at '{endpoint}'");
        }

        Ok(())
    }

    fn response(&mut self, py: Python<'_>, response: Py<PyAny>) -> PyResult<()> {
        let response_ref = response.bind(py);
        let correlation_id = response_ref.getattr("correlation_id")?;
        let key = Self::normalize_key(py, &correlation_id)?;

        if let Some(callback) = self.correlation_index.remove(&key) {
            let _ = callback.bind(py).call1((response,));
        } else {
            log::debug!("No callback for correlation_id {key}");
        }
        self.res_count += 1;
        Ok(())
    }

    #[pyo3(signature = (topic, handler, priority=0))]
    fn subscribe(
        &mut self,
        py: Python<'_>,
        topic: &str,
        handler: Py<PyAny>,
        priority: i32,
    ) -> PyResult<()> {
        if !handler.bind(py).is_callable() {
            return Err(PyValueError::new_err("handler must be callable"));
        }
        if priority < 0 {
            return Err(PyValueError::new_err("priority must be non-negative"));
        }
        let sub = Subscription {
            topic: topic.to_string(),
            handler,
            priority,
        };
        let key = sub.key();

        if self.subscriptions.contains_key(&key) {
            return Ok(());
        }

        let mut matches: Vec<String> = Vec::new();
        let patterns: Vec<String> = self.patterns.keys().cloned().collect();
        for pattern in patterns {
            if Self::is_matching(topic, pattern.as_str()) {
                let subs = self.patterns.entry(pattern.clone()).or_default();
                Self::insert_subscription_sorted(subs, sub.clone());
                matches.push(pattern);
            }
        }

        self.subscriptions.insert(
            key,
            SubscriptionEntry {
                subscription: sub,
                matches,
            },
        );
        self.resolved = false;
        Ok(())
    }

    fn unsubscribe(&mut self, topic: &str, handler: Py<PyAny>) -> PyResult<()> {
        let key = SubscriptionKey {
            topic: topic.to_string(),
            handler_ptr: handler.as_ptr() as usize,
        };
        let entry = match self.subscriptions.remove(&key) {
            Some(entry) => entry,
            None => return Ok(()),
        };

        for pattern in entry.matches {
            if let Some(subs) = self.patterns.get_mut(&pattern) {
                subs.retain(|sub| sub.key() != key);
            }
        }

        self.resolved = false;
        Ok(())
    }

    #[pyo3(signature = (topic, msg, external_pub=true))]
    fn publish(&mut self, py: Python<'_>, topic: &str, msg: Py<PyAny>, external_pub: bool) {
        let subs = self.patterns.get(topic).cloned();
        let subs = match subs {
            Some(existing) if self.resolved && !existing.is_empty() => existing,
            _ => {
                let resolved = self.resolve_subscriptions(topic);
                self.resolved = true;
                resolved
            }
        };

        for sub in subs {
            let _ = sub.handler.bind(py).call1((msg.clone_ref(py),));
        }

        if external_pub {
            let is_publishable = self.publishable_types.iter().any(|ty| {
                let ty_ref = ty.bind(py);
                msg.bind(py).is_instance(&ty_ref).unwrap_or(false)
            });

            if is_publishable {
                let mut payload: Option<Py<PyAny>> = None;

                if msg.bind(py).is_instance_of::<PyBytes>() {
                    payload = Some(msg.clone_ref(py));
                } else if let Some(serializer) = &self.serializer {
                    if let Ok(result) =
                        serializer.bind(py).call_method1("serialize", (msg.clone_ref(py),))
                    {
                        payload = Some(result.unbind());
                    }
                }

                if let Some(payload) = payload {
                    if let Some(database) = &self.database {
                        let db_ref = database.bind(py);
                        let is_closed = db_ref
                            .getattr("is_closed")
                            .ok()
                            .and_then(|method| method.call0().ok())
                            .and_then(|val| val.extract::<bool>().ok())
                            .unwrap_or(false);
                        if !is_closed {
                            let _ = db_ref.call_method1("publish", (topic, payload.clone_ref(py)));
                        }
                    }

                    for listener in &self.listeners {
                        let listener_ref = listener.bind(py);
                        let is_closed = listener_ref
                            .getattr("is_closed")
                            .ok()
                            .and_then(|method| method.call0().ok())
                            .and_then(|val| val.extract::<bool>().ok())
                            .unwrap_or(false);
                        if is_closed {
                            continue;
                        }
                        let _ = listener_ref.call_method1("publish", (topic, payload.clone_ref(py)));
                    }
                }
            }
        }

        self.pub_count += 1;
    }
}

#[pyfunction]
fn is_matching_py(topic: &str, pattern: &str) -> bool {
    is_matching(topic.as_bytes(), pattern.as_bytes())
}

#[pyfunction(name = "hmac_signature")]
fn py_hmac_signature(secret: &str, data: &str) -> PyResult<String> {
    hmac_signature(secret, data).map_err(to_value_error)
}

#[pyfunction(name = "rsa_signature")]
fn py_rsa_signature(private_key_pem: &str, data: &str) -> PyResult<String> {
    rsa_signature(private_key_pem, data).map_err(to_value_error)
}

#[pyfunction(name = "ed25519_signature")]
fn py_ed25519_signature(private_key: &[u8], data: &str) -> PyResult<String> {
    ed25519_signature(private_key, data).map_err(to_value_error)
}

#[pymodule]
fn _libflashcore(py: Python<'_>, m: &Bound<'_, PyModule>) -> PyResult<()> {
    pyo3::prepare_freethreaded_python();
    m.add_class::<UUID4>()?;
    m.add_class::<TraderId>()?;
    m.add_class::<TimeEvent>()?;
    m.add_class::<LiveClock>()?;
    m.add_class::<TestClock>()?;
    m.add_class::<Subscription>()?;
    m.add_class::<MessageBus>()?;
    m.add_function(wrap_pyfunction!(is_matching_py, m)?)?;
    m.add_function(wrap_pyfunction!(py_hmac_signature, m)?)?;
    m.add_function(wrap_pyfunction!(py_rsa_signature, m)?)?;
    m.add_function(wrap_pyfunction!(py_ed25519_signature, m)?)?;

    // Also make the module visible as flashcore.core.nautilus_pyo3 for compatibility
    let sys = PyModule::import(py, "sys")?;
    let modules = sys.getattr("modules")?;
    modules.set_item("flashcore._libflashcore", m)?;
    Ok(())
}
