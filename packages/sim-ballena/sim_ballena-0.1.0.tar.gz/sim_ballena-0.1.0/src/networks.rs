use pyo3::prelude::*;
use pyo3::exceptions::PyValueError;
use crate::neurons::Lif;
use crate::utils::{vec_of_tuples, sanity_check_syn, sanity_check_outputs};
use crate::simulation::simulate;
use crate::instances::Instance;
use crate::responses::Response;
use std::collections::HashSet;

/* ========================= */
/* ======== OBJECTS ======== */
/* ========================= */

#[derive(Clone)]
#[derive(Debug)]
pub struct Synapses{
    pub neu_post : usize,
    pub syn_idx  : usize,
}

/* ========================= */
/* ======= NETWORK ========= */
/* ========================= */

#[pyclass]
pub struct Network{
    // Netowrk topology
    neurons  : Vec<Lif>,
    syn_in  : Option<Vec<Vec<Synapses>>>,
    syn_net : Option<Vec<Vec<Synapses>>>,
    w_in    : Option<Vec<f64>>,
    w_net   : Option<Vec<f64>>,
    outputs : Option<Vec<usize>>,
    // description
    n_syn_in  : Option<usize>,
    n_syn_net : Option<usize>,
    // output config
    modes   : (bool, bool), // (VOLTAGES, SPIKES)

}

#[pymethods]
impl Network{
    /* ==================== */
    /*     CONSTRUCTOR      */
    /* ==================== */
    #[new]
    fn new(neurons: Vec<Lif>)->Self{
        Self{neurons, 
            syn_in  : None, 
            syn_net : None,
            w_in    : None, 
            w_net   : None, 
            outputs : None, 
            n_syn_in : None, 
            n_syn_net: None,
            modes    : (false, true)}
    }

    /* ==================== */
    /*   SET_SYNAPSES_IN    */
    /* ==================== */
    fn synapses_in<'py>(mut this: PyRefMut<'py, Self>,obj: &Bound<'_, PyAny>)->PyResult<PyRefMut<'py, Self>>{
        // check if conversion is possible
        let synapses = match vec_of_tuples::<usize>(obj){
            Ok(v)  => v,
            Err(e) => return Err(e)
        };

        // Weights are outdated
        this.w_in = None;

        if synapses.len()==0{{
            let structured_synapses:Vec<Vec<Synapses>> = Vec::new();
            this.syn_in = Some(structured_synapses);
            this.n_syn_in = Some(0);
            return Ok(this)
        }}
        // Sanity check
        let max_neu_pre = match sanity_check_syn(&synapses, this.neurons.len(), true){
            Ok(v)  => v,
            Err(e) => return Err(e)
        };

        // Build structured synapses and save
        let mut structured_synapses:Vec<Vec<Synapses>> = vec![Vec::new() ; max_neu_pre+1];
        for (idx, (neu_pre,neu_post)) in synapses.iter().enumerate(){
           structured_synapses[*neu_pre].push(Synapses{
                neu_post : *neu_post,
                syn_idx  : idx,
            })
        }

        this.syn_in  = Some(structured_synapses);
        this.n_syn_in = Some(synapses.len());

        Ok(this)
    }

    /* ===================== */
    /*   SET_SYNAPSES_NET    */
    /* ===================== */
    fn synapses_net<'py>(mut this: PyRefMut<'py, Self>,obj: &Bound<'_, PyAny>)->PyResult<PyRefMut<'py, Self>>{
        // check if conversion is possible
        let synapses = match vec_of_tuples::<usize>(obj){
            Ok(v)  => v,
            Err(e) => return Err(e)
        };

        // Weights are outdated
        this.w_net = None;

        // Check if list is empty
        if synapses.len()==0{{
            let structured_synapses:Vec<Vec<Synapses>> = Vec::new();
            this.syn_net = Some(structured_synapses);
            this.n_syn_net = Some(0);
            return Ok(this)
        }}
        // Sanity check
        let max_neu_pre = match sanity_check_syn(&synapses, this.neurons.len(), false){
            Ok(v)  => v,
            Err(e) => return Err(e)
        };
       
        // Build structured synapses and save
        let mut structured_synapses:Vec<Vec<Synapses>> = vec![Vec::new() ; max_neu_pre+1];
        for (idx, (neu_pre,neu_post)) in synapses.iter().enumerate(){
           structured_synapses[*neu_pre].push(Synapses{
                neu_post : *neu_post,
                syn_idx  : idx,
            })
        }

        this.syn_net  = Some(structured_synapses);
        this.n_syn_net = Some(synapses.len());

        Ok(this)
    }
    /* ===================== */
    /*    SET_WEIGHTS_IN     */
    /* ===================== */
    fn weights_in<'py>(mut this: PyRefMut<'py, Self>, weights:Vec<f64>)->PyResult<PyRefMut<'py,Self>>{
        match this.n_syn_in{
            Some(n) => {
                if weights.len()!=n{
                    let msg_err = format!("Number of synapses ({}) does not match with weights lenght ({})",
                                            n, weights.len());
                    return Err(PyValueError::new_err(msg_err))
                }
            },
            None => return Err(PyValueError::new_err("First you need to set input synapses"))
        }

        this.w_in = Some(weights);

        Ok(this)
    }

    /* ===================== */
    /*    SET_WEIGHTS_NET    */
    /* ===================== */
    fn weights_net<'py>(mut this: PyRefMut<'py, Self>, weights:Vec<f64>)->PyResult<PyRefMut<'py,Self>>{
        match this.n_syn_net{
            Some(n) => {
                if weights.len()!=n{
                    let msg_err = format!("Number of synapses ({}) does not match with weights lenght ({})",
                                            n, weights.len());
                    return Err(PyValueError::new_err(msg_err))
                }
            },
            None => return Err(PyValueError::new_err("First you need to set network synapses"))
        }

        this.w_net = Some(weights);

        Ok(this)
    }

    /* ===================== */
    /*      SET_OUPUPTS      */
    /* ===================== */
    fn outputs<'py>(mut this: PyRefMut<'py, Self>, outputs:Vec<usize>)->PyResult<PyRefMut<'py,Self>>{

        // No outputs
        if outputs.len()==0{
            return Err(PyValueError::new_err("Output list cannot be empty"));
        }
        // Sanity check
        if let Err(e) = sanity_check_outputs(&outputs, this.neurons.len()){
            return Err(e)
        }
        

        this.outputs = Some(outputs);
        Ok(this)
    }

    /* ===================== */
    /*     SET_MODALITY      */
    /* ===================== */
    fn mode<'py>(mut this: PyRefMut<'py, Self>, modes: Vec<String>)->PyResult<PyRefMut<'py,Self>>{
        let supported_modes:HashSet<String> = vec![String::from("VOLTAGES"),
                                                   String::from("SPIKES")].into_iter().collect();
                
        for mode in modes.iter(){
            if !supported_modes.contains(mode){
                let msg = format!("Supported modes: [VOLTAGES, SPIKES]. {} not supported",mode);
                return Err(PyValueError::new_err(msg))
            }
        }

        if modes.len()==0{
            return Err(PyValueError::new_err("At least one mode must be especified"))
        }

        this.modes = (modes.contains(&"VOLTAGES".into()),
                      modes.contains(&"SPIKES".into()));
        

        Ok(this)
    }

    /* ===================== */
    /*        __STR__        */
    /* ===================== */
    fn __str__(&self)->String{
        let mut view = format!("Network( Neu:{}",self.neurons.len());

        if let Some(n_syn_in) = self.n_syn_in{
            match self.w_in{
                Some(_) => view += &format!(", Syn_in(w):{}",n_syn_in),
                None    => view += &format!(", Syn_in:{}",n_syn_in)
            }
            
        }

        if let Some(n_syn_net) = self.n_syn_net{
            match self.w_net{
                Some(_) => view += &format!(", Syn_net(w):{}",n_syn_net),
                None    => view += &format!(", Syn_net:{}",n_syn_net)
            }
        }

        if let Some(outputs) = &self.outputs{
            view += &format!(", Outputs:{}",outputs.len());
        }

        view += " )";
        view
    }

    fn __repr__(&self)->String{
        self.__str__()
    }

    /* ===================== */
    /*       VOLTAGES        */
    /* ===================== */
    fn get_voltages(&self)->Vec<f64>{
        self.neurons.iter().map(|n|n.get_voltage()).collect()
    }

    /* ===================== */
    /*      SIMULATE         */
    /* ===================== */
    fn simulate(&mut self, instance: PyRef<'_, Instance>, max_time:f64)->PyResult<Response>{
        simulate(self, instance, max_time)
    }

}


impl Network{
    pub fn get_neurons(&mut self)->&mut Vec<Lif>{
        &mut self.neurons
    }
    pub fn get_syn_in(&self)->Option<&Vec<Vec<Synapses>>>{
        self.syn_in.as_ref()
    }
    pub fn get_syn_net(&self)->Option<&Vec<Vec<Synapses>>>{
        self.syn_net.as_ref()
    }
    pub fn get_w_in(&self)-> Option<&Vec<f64>>{
        self.w_in.as_ref()
    }
    pub fn get_w_net(&self)-> Option<&Vec<f64>>{
        self.w_net.as_ref()
    }
    pub fn get_outputs(&self)-> Option<&Vec<usize>>{
        self.outputs.as_ref()
    }
    pub fn get_modes(&self)->(bool,bool){
        self.modes.clone()
    }

}