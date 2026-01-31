use pyo3::prelude::*;
use pyo3::exceptions::PyValueError;

const DEFAULT_V_THRES :f64 = -55.0;
const DEFAULT_V_REST  :f64 = -70.0;
const DEFAULT_V_RESET :f64 = -70.0;
const DEFAULT_TAU     :f64 = 10.0;
const DEFAULT_REFRACT :f64 = 1.0;


/* ========================== */
/* ========= LIF ============ */
/* ========================== */

#[derive(Clone)]
#[pyclass]
pub struct Lif{
    // Model parameters
    v_thres  :f64,
    v_rest    :f64,
    v_reset   :f64,
    tau       :f64,
    t_refract :f64,
    // Dinamics
    voltage      : f64,
    last_updated : f64,
    last_spike   : Option<f64>,
    activity_win : Option<(f64,f64)>,   // (start,end)
}

/* ============= */
/* LIF INTERFACE */
/* ============= */
#[pymethods]
impl Lif{
    #[new]
    pub fn new()->Self{
        Self{v_thres      : DEFAULT_V_THRES, 
             v_rest       : DEFAULT_V_REST,
             v_reset      : DEFAULT_V_RESET,
             tau          : DEFAULT_TAU, 
             t_refract    : DEFAULT_REFRACT,
             voltage      : DEFAULT_V_REST, 
             last_updated : 0.0,
             last_spike   : None,
             activity_win : None,
            }
    }

    fn __str__(&self)->String{
        format!("Lif(v_thres:{}, v_rest:{}, v_reset:{}, tau:{}, t_refractory:{} )",
         self.v_thres, self.v_rest, self.v_reset, self. tau, self.t_refract)
    }

    fn __repr__(&self)->String{
        self.__str__()
    }

    fn repeat(&self,n:usize)->Vec<Self>{
        vec![self.clone() ; n]
    }

    /* GETTERS */
    pub fn get_voltage(&self)->f64{
        self.voltage
    }

    pub fn get_tau(&self)->f64{
        self.tau
    }

    pub fn get_v_rest(&self)->f64{
        self.v_rest
    }

    pub fn get_v_thres(&self)->f64{
        self.v_thres
    }

    pub fn get_v_reset(&self)->f64{
        self.v_reset
    }
    
    pub fn get_t_refractory(&self)->f64{
        self.t_refract
    }

    /* SETTERS */
    fn tau(mut this: PyRefMut<'_, Self>, tau:f64)->PyRefMut<'_, Self>{
        this.tau = tau;
        this
    }

    fn v_rest(mut this: PyRefMut<'_, Self>, v_rest:f64)->PyRefMut<'_, Self>{
        this.v_rest = v_rest;
        this
    }

    fn v_thres(mut this: PyRefMut<'_, Self>, v_thres:f64)->PyRefMut<'_, Self>{
        this.v_thres = v_thres;
        this
    }

    fn v_reset(mut this: PyRefMut<'_, Self>, v_reset:f64)->PyRefMut<'_, Self>{
        this.v_reset = v_reset;
        this
    }

    fn t_refractory(mut this: PyRefMut<'_, Self>, t_refractory:f64)->PyRefMut<'_, Self>{
        this.t_refract = t_refractory;
        this
    }

    fn activity_window(mut this: PyRefMut<'_, Self>, start:f64, end:f64)->PyResult<PyRefMut<'_,Self>>{
        if end <= start{
            return Err(PyValueError::new_err("End time must be greater than start time"));
        }
        this.activity_win = Some((start, end));
        Ok(this)
    }
}

/* ============ */
/* LIF DYNAMICS */
/* ============ */
impl Lif{
    /* leak */
    pub fn update(&mut self, t:f64){
        let dt = t-self.last_updated;
        let new_v = self.v_rest + (self.voltage - self.v_rest)*(-dt/self.tau).exp();
        self.voltage = new_v;
        self.last_updated = t;
    }
    /* integrate */
    pub fn integrate(&mut self, t:f64, w:f64)->bool{

        // Outside activity window the neuron is disconected
        if let Some((start,end)) = self.activity_win{
            if t<start || t>end{
                self.update(t);
                return false
            }
        }
        // refractory time
        if let Some(last_spike) = self.last_spike{
            if t<=last_spike+self.t_refract{
                return false
            }
        }
        // update voltage
        self.update(t);
        self.voltage += w;
        return self.voltage > self.v_thres
    }
    /* fire */
    pub fn spike(&mut self, t:f64){
        self.voltage = self.v_reset; 
        self.last_spike = Some(t);
    }

    /* reset state */
    pub fn reset_state(&mut self){
        self.voltage         = self.v_rest;
    }
}