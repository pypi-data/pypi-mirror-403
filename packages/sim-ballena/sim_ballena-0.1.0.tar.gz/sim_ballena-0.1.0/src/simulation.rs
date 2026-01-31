
use pyo3::prelude::*;
use pyo3::exceptions::PyRuntimeError;
use std::collections::HashSet;
use crate::networks::Network;
use crate::instances::Instance;
use crate::responses::Response;


/* =================== */
/*   EVENTS CONTROL    */
/* =================== */

enum EventType{
    SpikeIn,
    SpikeNet
}

struct EventBuffer<'a>{
    spikes_in: &'a Vec<(f64,usize)>,    // asc order
    spikes_net : Vec<(f64,usize)>,      // desc order
    idx_in     : usize,
    sorted     : bool,
}

impl<'a> EventBuffer<'a>{
    fn new(spikes_in:&'a Vec<(f64,usize)>, buffer_capacity:usize)->Self{
        Self{spikes_in, 
            spikes_net : Vec::with_capacity(buffer_capacity), 
            idx_in     : 0,
            sorted     : false
        }
    }

    fn push_spike_net(&mut self, event:(f64,usize)){
        self.spikes_net.push( event );
        self.sorted = false;
    }

    fn get(&mut self)->Option<(EventType, (f64,usize))>{

        if !self.sorted{
            self.spikes_net.sort_by( |a,b|b.0.partial_cmp(&a.0).unwrap() );
            self.sorted = true;
        }

        match (self.spikes_in.get(self.idx_in), self.spikes_net.last()){
            (Some(spk_in), Some(spk_net)) =>{
                if spk_in.0 < spk_net.0{
                    self.idx_in += 1;
                    Some( (EventType::SpikeIn, *spk_in) )
                }else{

                    Some( (EventType::SpikeNet, self.spikes_net.pop().unwrap()) )
                }
            },
            (Some(spk_in), None) => {
                self.idx_in += 1;
                Some( (EventType::SpikeIn, *spk_in) )
            },
            (None, Some(_)) => {
                Some( (EventType::SpikeNet, self.spikes_net.pop().unwrap()) )
            },
            (None,None) => None
        }
    }
}

/* ================= */
/*    SIMULATION     */
/* ================= */

pub fn simulate(network:&mut Network, instance: PyRef<'_, Instance>, max_time:f64)->PyResult<Response>{


    /* ================================= */
    /* PREPARE EVENT BUFFER AND RESPONSE */
    /* ================================= */
    let outputs = match network.get_outputs(){
        Some(o) => o.clone(),
        None    => return Err(PyRuntimeError::new_err("Outputs not defined"))
    };
    
    let mut events   = EventBuffer::new( instance.get(), network.get_neurons().len() );
    let mut response = Response::new( network.get_outputs().unwrap().clone(), network.get_modes() );

    /* =========================== */
    /* GET ELEMENTS OF THE NETWORK */
    /* =========================== */
    let neurons     = network.get_neurons().as_mut_ptr();

    let syn_in  = match network.get_syn_in(){
        Some(syn) => syn,
        None => return Err(PyRuntimeError::new_err("Input synapses not defined"))
    };
    let syn_net = match network.get_syn_net(){
        Some(syn) => syn,
        None => return Err(PyRuntimeError::new_err("Network synapses not defined"))
    };

    let w_in = match network.get_w_in(){
        Some(w) => w,
        None    => return Err(PyRuntimeError::new_err("Input weights not defined"))
    };

    let w_net = match network.get_w_net(){
        Some(w) => w,
        None    => return Err(PyRuntimeError::new_err("Network weights not defined"))
    };

    let outputs_set:HashSet<usize> = outputs.iter().cloned().collect();


    // First measure
    unsafe{
        for o in outputs.iter().cloned(){
            let neuron = neurons.add(o);
            response.save_voltage( o, 0.0, (*neuron).get_voltage() );  
        }
    }

    /* ============== */
    /*    MAIN LOOP   */
    /* ============== */
    while let Some(event) = events.get(){

        let (event_type, (time, id_pre)) = event;
        
        // max time then leave
        if time>max_time{
            break;
        }

        // select synapses input of net
        let synapses =  match event_type{
            EventType::SpikeIn  => syn_in,
            EventType::SpikeNet => syn_net,
        };

        // synapses can be out of range in case of unkwown input ids
        let synapses_to_inform = match synapses.get(id_pre){
            Some(syn) => syn,
            None      => continue
        };
        
        // Only save measures if the event has been procceced 
        // and the neuron changed and needs to be tracked
        let mut track_voltage  : HashSet<usize> = HashSet::new();
        let mut _track_spikes  : HashSet<usize> = HashSet::new();
        let mut neuron_spike   : HashSet<usize> = HashSet::new(); 


        // for every neuron to inform
        for syn in synapses_to_inform{
            let w = match event_type{
                EventType::SpikeIn  => w_in.get( syn.syn_idx ).unwrap(),
                EventType::SpikeNet => w_net.get( syn.syn_idx ).unwrap()
            };
            // here we need to modify the neuron state, 
            // but we ensure that synapses are not modified
            unsafe{
                let neuron = neurons.add(syn.neu_post);
                let spike  = (*neuron).integrate(time,*w);
                if spike{
                    neuron_spike.insert( syn.neu_post );
                }

                if outputs_set.contains( &syn.neu_post ){
                    track_voltage.insert( syn.neu_post );
                }
                
                
            }
        }

        /* ============================= */
        // the event has been proccesed, 
        // its time to record
        /* ============================= */
        unsafe{
            // spike 
            for neu_idx in neuron_spike{
                let neuron = neurons.add(neu_idx);
                if outputs_set.contains(&neu_idx){
                    // (*neuron).save_marker(time);
                    response.save_voltage( neu_idx, time, (*neuron).get_voltage() );
                }
                (*neuron).spike(time);
                events.push_spike_net( (time, neu_idx) );

                // save spike if neuron is output and spiked
                if outputs_set.contains(&neu_idx){
                    response.save_spike(neu_idx, time);
                }
            } 
            // sabe voltage if neuron is output
            for neu_idx in track_voltage{
                let neuron = neurons.add(neu_idx);
                response.save_voltage( neu_idx, time, (*neuron).get_voltage() );              
            }
        }
        
    }
    /* ==================== */
    /*   AFTER SIMULATION   */
    /* ==================== */

    // last measure
    unsafe{
        for o in outputs.iter().cloned(){
            let neuron = neurons.add(o);
            (*neuron).update(max_time);
            response.save_voltage( o, max_time, (*neuron).get_voltage() );  
        }
    }

    /* ================ */
    /*  build response  */
    /* ================ */
    let neurons     = network.get_neurons();

    let tau_list:Vec<f64>     = outputs.iter().map(|&o|neurons.get(o).unwrap().get_tau()).collect();
    let v_rest_list:Vec<f64>  = outputs.iter().map(|&o|neurons.get(o).unwrap().get_v_rest()).collect();
    
    response = response.max_time( max_time )
                       .v_rest_list( v_rest_list )
                       .tau_list( tau_list );


    // voltages
    // let neurons = network.get_neurons();
    // let voltage_markers:Vec<Vec<VoltageMarker>>  = outputs.iter().map(|&o|neurons.get(o).unwrap().get_voltage_markers()).collect();


    // let mut res = Response::new( outputs.clone() );
    // res.set_max_time(max_time);
    // res.set_voltage_markers(voltage_markers);
    // res.set_tau_list( tau_list );
    // res.set_v_rest_list( v_rest_list );

    // spikes
    // let spikes:Vec<Vec<f64>> = outputs.iter().map(|&o|neurons.get(o).unwrap().get_spikes()).collect();
    // res.set_spikes( spikes );

    // reset all neuron states
    for neu in neurons{{
        neu.reset_state();
    }}
    Ok(response)
}

