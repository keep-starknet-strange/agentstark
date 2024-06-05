use starknet::SyscallResultTrait;
use starknet::account::Call;
use starknet::syscalls::call_contract_syscall;


pub fn execute_single_call(call: Call) -> Span<felt252> {
    let Call { to, selector, calldata } = call;
    call_contract_syscall(to, selector, calldata).unwrap_syscall()
}

pub fn execute_calls(mut calls: Array<Call>) -> Array<Span<felt252>> {
    let mut res = ArrayTrait::new();
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