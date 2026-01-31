use pyo3::prelude::*;
use pyo3::exceptions::PyValueError;
use crate::utils::vec_of_tuples;
use rand_distr::{Exp, Distribution};

/* ================ */
/* === INSTANCE === */
/* ================ */

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

impl Instance{
    pub fn from_poisson(spikes:Vec<(f64,usize)>)->Self{
        Self{spikes}
    }
}

/* ================= */
/* ==== POISSON ==== */
/* ================= */

#[pyclass]
pub struct PoissonGenerator{
    max_time    : f64,
    spike_times : Vec<Vec<f64>>,
}

#[pymethods]
impl PoissonGenerator{
    #[new]
    fn new(rates: Vec<f64>, max_time:f64)->Self{
        let mut spike_times:Vec<Vec<f64>> = Vec::new();
        for rate in rates{
            spike_times.push( Self::poisson_process(rate, max_time)  );
        }
        Self{max_time, spike_times}
    }

    fn to_instance(&self)->Instance{
        let mut all_spikes:Vec<(f64,usize)> = Vec::new();
        for (ch,spikes) in self.spike_times.iter().enumerate(){
            let instance_view:Vec<(f64,usize)> = spikes.iter().map(|t|(*t,ch)).collect();
            all_spikes.extend( instance_view );
        }
        Instance::from_poisson( all_spikes )
    }

    fn get_spikes(&self)->Vec<Vec<f64>>{
        self.spike_times.clone()
    }

    fn concat<'py>(mut this:PyRefMut<'py, Self>, other:&PoissonGenerator)->PyResult<PyRefMut<'py,Self>>{
        
        // check both generators have same dimentions
        let mut spikes_other = other.get_spikes();
        if spikes_other.len() != this.spike_times.len(){
            return Err(PyValueError::new_err("PoissonGenerator must have the same number of inputs"))
        }
        // offset
        for ch in spikes_other.iter_mut(){
            for spk in ch.iter_mut(){
                *spk += this.max_time;
            }
        }
        // concat
        for ch_idx in 0..spikes_other.len(){
            this.spike_times[ch_idx].extend( spikes_other[ch_idx].clone() );
        }
        this.max_time += other.get_max_time();
        Ok(this)
    }

    fn __str__(&self)->String{
        format!("PoissonGenerator(n_inputs:{}, max_time:{})", self.spike_times.len(), self.max_time)
    }

    fn __repr__(&self)->String{
        self.__str__()
    }

}

impl PoissonGenerator{
    fn poisson_process(rate:f64, max_time:f64)->Vec<f64>{
        let mut rng = rand::rng();
        let poi = Exp::new(rate).unwrap();

        let mut spikes:Vec<f64> = Vec::new();
        let mut t = poi.sample( &mut rng );
        while t<max_time{
            spikes.push(t);
            t += poi.sample( &mut rng );
        }
        spikes
    }

    pub fn get_max_time(&self)->f64{
        self.max_time
    }


}