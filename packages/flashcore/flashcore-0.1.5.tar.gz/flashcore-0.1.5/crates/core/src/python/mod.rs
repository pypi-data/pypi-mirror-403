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

//! Minimal Python helpers required by the flashcore bindings.

use pyo3::{Py, PyAny, Python, conversion::IntoPyObjectExt};

/// Safely clones a Python object by acquiring the GIL and properly managing reference counts.
#[must_use]
pub fn clone_py_object(obj: &Py<PyAny>) -> Py<PyAny> {
    Python::attach(|py| obj.clone_ref(py))
}

/// Extend `IntoPyObjectExt` helper trait to unwrap `Py<PyAny>` after conversion.
pub trait IntoPyObjectNautilusExt<'py>: IntoPyObjectExt<'py> {
    /// Convert `self` into a [`Py<PyAny>`] while *panicking* if the conversion fails.
    #[inline]
    fn into_py_any_unwrap(self, py: Python<'py>) -> Py<PyAny> {
        self.into_py_any(py)
            .expect("Failed to convert type to Py<PyAny>")
    }
}

impl<'py, T> IntoPyObjectNautilusExt<'py> for T where T: IntoPyObjectExt<'py> {}
