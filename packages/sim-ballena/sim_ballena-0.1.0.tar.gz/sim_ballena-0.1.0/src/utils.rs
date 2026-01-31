
use pyo3::prelude::*;
use pyo3::types::PySequence;
use pyo3::exceptions::PyValueError;

use std::collections::HashSet;

/* ===================== */
/*     VEC_OF_TUPLES     */
/* ===================== */
pub fn vec_of_tuples<T>(obj: &Bound<'_, PyAny>)->PyResult<Vec<(T,usize)>> 
where for<'a, 'py> T: FromPyObject<'a, 'py>{

    // First try with a list of tuples
    if let Ok(vec) = obj.extract::<Vec<(T, usize)>>() {
        return Ok(vec);
    }

    // If not possible, try with a list of list
    let seq                          = obj.cast::<PySequence>()?;
    let n                            = seq.len()?;
    let mut resultado:Vec<(T,usize)> = Vec::with_capacity(n);

    for i in 0..n{
        let item = seq.get_item(i)?;

        let len_method = item.getattr("__len__")?;
        let py_len = len_method.call0()?;
        if py_len.extract::<usize>()? == 2{

            let e1_ = item.get_item(0)?;
            let e2_ = item.get_item(1)?;

            if let Ok(e1) = e1_.extract::<T>(){
                if let Ok(e2) = e2_.extract::<usize>(){
                    resultado.push((e1,e2));
                    continue;
                }
            }
        }
        return Err(PyValueError::new_err("Is not possible to convert the sequence. Please try with a list of tuples of 2 elements. [(numbe,number)...]"))
    }
    Ok(resultado)
}


/* ===================== */
/*   SANITY CHECK SYN    */
/* ===================== */
pub fn sanity_check_syn(synapses:&Vec<(usize,usize)>, n_neu:usize, is_input:bool)->PyResult<usize>{
        
    // Check consistency
    let max_neu_pre  = synapses.iter().map(|syn|syn.0).max().unwrap();
    let max_neu_post = synapses.iter().map(|syn|syn.1).max().unwrap();
    
    if max_neu_pre >= n_neu && !is_input {
        let msg_error = format!("Max pre-synaptic id ({}) must be lower than the number of neurons ({})",
                                max_neu_pre, n_neu);
        return Err(PyValueError::new_err(msg_error))
    }

    if max_neu_post >= n_neu{
        let msg_error = format!("Max post-synaptic id ({}) must be lower than the number of neurons ({})",
                                max_neu_post, n_neu);
        return Err(PyValueError::new_err(msg_error))
    }
    // Check self loops
    if synapses.iter().filter(|(a,b)|a==b).count() != 0 && !is_input{
        return Err(PyValueError::new_err("Synapses with self-loops are not allowed"))
    }

    // Check duplicates
    let mut check_set:HashSet<(usize,usize)> = HashSet::with_capacity(synapses.len());
    if !synapses.iter().all(|syn|check_set.insert(*syn)){
        return Err(PyValueError::new_err("Repeated synapses are not allowed"))
    }

    Ok(max_neu_pre)
}

/* ====================== */
/*  SANITY CHECK OUTPUTS  */
/* ====================== */
pub fn sanity_check_outputs(outputs:&Vec<usize>, n_neu:usize)->PyResult<()>{
    // Check outputs > neurons
    let max_output = *outputs.iter().max().unwrap();
    if max_output >= n_neu{
        let msg_err = format!("The max output id({}) must be lower than the number of neurons({})",
                                max_output, n_neu);
        return Err(PyValueError::new_err(msg_err))
    }
    // Check repeated
    let mut output_set:HashSet<usize> = HashSet::with_capacity(outputs.len());
    if !outputs.iter().all(|o|output_set.insert(*o)){
        return Err(PyValueError::new_err("Repeated outputs are not allowed"))
    }
    Ok(())
}
