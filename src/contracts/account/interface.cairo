// use array::{ArrayTrait, SpanTrait};
// use starknet::ContractAddress;

// #[derive(Serde, Drop)]
// struct Call {
//     to: ContractAddress,
//     selector: felt252,
//     calldata: Array<felt252>
// }

// // Account Standard Interface
// #[starknet::interface]
// trait IAccount {
//     fn __execute__(calls: Array<Call>) -> Array<Span<felt252>>;
//     fn __validate__(calls: Array<Call>) -> felt252;
//     fn __validate_declare__(class_hash: felt252) -> felt252;
//     fn is_valid_signature(message: felt252, signature: Array<felt252>) -> u32;
//     fn supports_interface(interface_id: u32) -> bool;
// }