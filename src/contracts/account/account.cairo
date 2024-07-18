#[starknet::contract(account)]
mod AgentStarkAccount{
    use openzeppelin::account::AccountComponent;
    use openzeppelin::account::interface::ISRC6;
    use openzeppelin::introspection::src5::SRC5Component;
    use starknet::account::Call;
    use starknet::ContractAddress;
    use starknet::Felt252TryIntoContractAddress;
    use core::starknet::{get_tx_info, SyscallResultTrait};
    use agentstark::utils::utils::{execute_single_call, execute_calls};
    
    component!(path: AccountComponent, storage: account, event: AccountEvent);
    component!(path: SRC5Component, storage: src5, event: SRC5Event);

    //
    // Storage
    //

    #[storage]
    struct Storage {
        #[substorage(v0)]
        account: AccountComponent::Storage,
        #[substorage(v0)]
        src5: SRC5Component::Storage,
    }

    //
    // Events
    //

    #[event]
    #[derive(Drop, starknet::Event)]
    enum Event {
        #[flat]
        AccountEvent: AccountComponent::Event,
        #[flat]
        SRC5Event: SRC5Component::Event,
    }

    //
    // SRC6 impl
    //

    #[abi(embed_v0)]
    impl ISRC6Impl of ISRC6<ContractState> {
        fn __execute__(self: @ContractState, calls: Array<Call>) -> Array<Span<felt252>> {
            execute_calls(calls)
        }

        fn __validate__(self: @ContractState, calls: Array<Call>) -> felt252 {
            let tx_info = get_tx_info().unbox();
            let signature = tx_info.signature.snapshot.clone();
            let hash = tx_info.transaction_hash;

            assert!(self.is_valid_signature(:hash, :signature) == 1);
            starknet::VALIDATED
        }

        fn is_valid_signature(
            self: @ContractState, hash: felt252, signature: Array<felt252>
        ) -> felt252 {
            1 // TODO: add agent signature verification 
        }
    }
}