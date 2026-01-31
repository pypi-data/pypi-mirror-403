use pyo3::prelude::*;
use crate::utils::vec_of_tuples;

#[pyclass]
pub struct Instance{
    spikes: Vec<(f64,usize)>
}

#[pymethods]
impl Instance{
    #[new]
    fn new(obj: &Bound<'_,PyAny>)->PyResult<Self>{
        let mut spikes = match vec_of_tuples::<f64>(obj){
            Ok(v)  => v,
            Err(e) => return Err(e)
        };


        spikes.sort_by(|a,b|a.0.partial_cmp(&b.0).unwrap());

        Ok(Self{spikes})
    }

    fn __str__(&self)->String{
        format!("Input(count={})",self.spikes.len())
    }

    fn __repr__(&self)->String{
        self.__str__()
    }

    pub fn get(&self)->&Vec<(f64,usize)>{
        &self.spikes
    }
}

