
mod networks;
mod neurons;
mod simulation;
mod instances;
mod utils;
mod responses;

use pyo3::prelude::*;


#[pymodule]
fn sim_ballena(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<neurons::Lif>()?;
    m.add_class::<networks::Network>()?;
    m.add_class::<instances::Instance>()?;
    // m.add_function( wrap_pyfunction!(networks::network,m)? )?;

    Ok(())
}




