use pyo3::prelude::*;
use pyo3::exceptions::PyRuntimeError;

const DEFAULT_RESOLUTION:f64 = 0.01;
const MAX_PRECISION     :f64 = 100_000.0;

/* ========================== */
/* ======= OBJECTS  ========= */
/* ========================== */
#[derive(Clone)]
struct VoltageMarker{
    pub t : f64,
    pub v : f64,
    pub id: usize,
}

struct SpikeMarker{
    pub t : f64,
    pub id: usize
}

/* ========================== */
/* ======= RESPONSE  ======== */
/* ========================== */
#[pyclass]
pub struct Response{
    // rec
    modes   : (bool,bool), //(VOLTAGE, SPIKES)
    voltages: Vec<VoltageMarker>,
    spikes  : Vec<SpikeMarker>,
    outputs : Vec<usize>,

    // voltage response
    resolution       : f64,
    max_time         : Option<f64>,
    simulation_times : Option<Vec<f64>>,
    tau_list         : Option<Vec<f64>>,
    v_rest_list      : Option<Vec<f64>>,
}

/* ========================== */
/* ======= METHODS  ========= */
/* ========================== */
impl Response{
    /* =========== */
    /* CONSTRUCTOR */
    pub fn new(outputs:Vec<usize>, modes:(bool,bool))->Self{

        let voltages:Vec<VoltageMarker> = {
            if modes.0{ Vec::with_capacity( 1000*outputs.len() ) }
            else{ Vec::new() }};
        let spikes:Vec<SpikeMarker> = {
            if modes.1{ Vec::with_capacity( 100*outputs.len() ) }
            else{ Vec::new() }
        };

        Self{modes,
            voltages,
            spikes,
            outputs         : outputs,
            resolution      : DEFAULT_RESOLUTION,
            max_time        : None,
            simulation_times: None,
            v_rest_list     : None,
            tau_list        : None,
        }
    }
    /* ======= */
    /* SETTERS */
    pub fn max_time(mut self, max_time:f64)->Self{
        self.max_time = Some(max_time);
        self
    }

    pub fn v_rest_list(mut self, v_rest_list:Vec<f64>)->Self{
        if v_rest_list.len() != self.outputs.len(){
            panic!("v_rest list size don't match with the outputs list size");
        }
        self.v_rest_list = Some(v_rest_list);
        self
    }

    pub fn tau_list(mut self, tau_list:Vec<f64>)->Self{
        if tau_list.len() != self.outputs.len(){
            panic!("Tau list size don't match with the outputs list size");
        }
        self.tau_list = Some(tau_list);
        self
    }



    /* ============== */
    /* MEMORY METHODS */
    pub fn save_voltage(&mut self, id:usize, t:f64, v:f64){
        if self.modes.0{
            self.voltages.push(VoltageMarker{t,v,id});
        }
    }

    pub fn save_spike(&mut self, id:usize, t:f64){
        if self.modes.1{
            self.spikes.push(SpikeMarker{t,id});
        }
    }
    /* ============ */
    /* CALCULATIONS */
    fn set_simulation_times(&mut self){
        match self.max_time{
            Some(max_time) => {
                let n_measures = (max_time/self.resolution) as usize;
                let mut times:Vec<f64> = Vec::with_capacity(n_measures);
                let mut t = 0.0;
                for _ in 0..n_measures{
                    times.push( (MAX_PRECISION*t).round()/MAX_PRECISION );
                    t += self.resolution;
                }
                self.simulation_times = Some(times)  
            },
            None => panic!("Can't set simulation time without setting max_time first")
        }
    }

    fn extract_voltage_serie(&self, 
                            marker_serie     : Vec<&VoltageMarker>, 
                            simulation_times : &Vec<f64>,
                            tau              : f64, 
                            v_rest           : f64)->Vec<f64>{

        let mut v_serie:Vec<f64> = Vec::with_capacity( simulation_times.len() );

        let mut idx_maker = 0;
        let mut current_marker: &VoltageMarker = marker_serie.get(0).unwrap();
        let mut next_marker   : &VoltageMarker = marker_serie.get(1).unwrap();
        for t in simulation_times{

            if next_marker.t <= *t{
                current_marker = next_marker;
                idx_maker += 1;
                next_marker = match marker_serie.get(idx_maker+1){
                    Some(marker) => marker,
                    None         => next_marker
                };
            }

            let dt = t-current_marker.t;
            let v  = v_rest + (current_marker.v - v_rest)*(-dt/tau).exp();
            v_serie.push(v);

        }
        v_serie 
    }
}

/* ========================== */
/* ======= INTERFACE  ======= */
/* ========================== */
#[pymethods]
impl Response{
    // ==================
    //  Check outputs
    fn outputs(&self)->Vec<usize>{
        self.outputs.clone()
    }

    // ==================
    //  Spikes response
    fn spikes(&self)->PyResult<Vec<Vec<f64>>>{
        if !self.modes.1{
            return Err(PyRuntimeError::new_err("Spikes response is not available for this network"))
        }

        let mut spikes:Vec<Vec<f64>> = Vec::with_capacity( self.outputs.len() );

        for o in self.outputs.iter(){
            let s_o:Vec<&SpikeMarker> = self.spikes.iter().filter(|s|s.id==*o).collect();
            spikes.push( s_o.iter().map(|s|s.t).collect() );
        }
        
        Ok(spikes)
    }

    // ==================
    //  Voltage response
    fn voltages(&mut self)->PyResult<Vec<Vec<f64>>>{
        if !self.modes.0{
            return Err(PyRuntimeError::new_err("Voltage response is not available for this network"))
        }
        let mut voltages:Vec<Vec<f64>> = Vec::with_capacity( self.outputs.len() );
        let simulation_times = match &self.simulation_times{
            Some(st) => st,
            None     => {
                self.set_simulation_times();
                self.simulation_times.as_ref().unwrap()
            }
        };

        let tau_list          = self.tau_list.as_ref().unwrap();
        let v_rest_list       = self.v_rest_list.as_ref().unwrap();

        for i in 0..self.outputs.len(){
            let markers_serie:Vec<&VoltageMarker> = self.voltages.iter()
                                                                .filter(|vm|vm.id==i)
                                                                .collect();

            let tau           = *tau_list.get(i).unwrap();
            let v_rest        = *v_rest_list.get(i).unwrap();
            voltages.push( self.extract_voltage_serie(markers_serie, simulation_times, tau, v_rest) );
        }

        Ok(voltages)

    }
    // ==================
    //    Time response
    fn time(&mut self)->PyResult<Vec<f64>>{
        if !self.modes.0{
            return Err(PyRuntimeError::new_err("Time is not available for network without voltage response"))
        }
        match &self.simulation_times{
            Some(simulation_times) => Ok(simulation_times.iter().cloned().collect()),
            None => {
                self.set_simulation_times();
                Ok(self.simulation_times.as_ref().unwrap().iter().cloned().collect())
            }
        }
    }

    // ==================
    //   Set resolution
    fn set_resolution(mut this:PyRefMut<'_, Self>, new_resolution:f64)->PyRefMut<'_, Self>{
        this.resolution = new_resolution;
        this
    }

    // ==================
    //     __STR__
    fn __str__(&self)->String{
        let mut view = String::from("Response(");
        if self.modes.0{
            view += &String::from("V");
            if self.modes.1{
                view += &String::from(",")
            }
        }
        if self.modes.1{
            view += &String::from("Spk");
        }
        view += &String::from(")");
        view
    }

    fn __repr__(&self)->String{
        self.__str__()
    }
}


