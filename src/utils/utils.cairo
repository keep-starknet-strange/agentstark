use starknet::SyscallResultTrait;
use starknet::account::Call;
use starknet::syscalls::call_contract_syscall;

const verify_and_register_fact: felt252 = selector!("verify_and_register_fact");
const is_valid: felt252 = selector!("is_valid");
const verifier_address: felt252 = 0x0274d8165a19590bdeaa94d1dd427e2034462d7611754ab3e15714a908c60df7;

pub fn execute_single_call(call: Call) -> Span<felt252> {
    let Call { to, selector, calldata } = call;
    call_contract_syscall(to, selector, calldata).unwrap_syscall()
}

// TODO: edit the flow, because the proof call and the rest of the calls will 
// most likely be part of different transaction. Once the proof is verified,
// the fact is registered, and the agent can check if a fact is valid. In this
// case, the agent will be able to execute the rest of the calls. 
pub fn execute_verifier_call(call: Call) -> Span<felt252> {
    let Call { to, selector, calldata } = call;
    assert!(to == verifier_address.try_into().unwrap());
    assert!(selector == verify_and_register_fact || selector == is_valid);
    call_contract_syscall(to, selector, calldata).unwrap_syscall()
}

pub fn execute_calls(mut calls: Array<Call>) -> Array<Span<felt252>> {
    let mut res = ArrayTrait::new();
    match calls.pop_front() {
        Option::Some(call) => {
            let _res = execute_verifier_call(call);
            res.append(_res);
        },
        Option::None(_) => { },
    };
    loop {
        match calls.pop_front() {
            Option::Some(call) => {
                let _res = execute_single_call(call);
                res.append(_res);
            },
            Option::None(_) => { break (); },
        };
    };
    res
}