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

    const view: felt252 = selector!("view");
    const storage_address: felt252 = 0x07284f04b63261283c6fb00867a078b449ae6ffe2b27a0cdc7ad091ab2ca674a;
    const erc20_address: felt252 = 0x07284f04b63261283c6fb00867a078b449ae6ffe2b27a0cdc7ad091ab2ca674a;

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
            self.account.__execute__(:calls)
        }

        fn __validate__(self: @ContractState, calls: Array<Call>) -> felt252 {
            let tx_info = get_tx_info().unbox();
            let _signature = tx_info.signature.snapshot.clone();
            let _hash = tx_info.transaction_hash;

            let mut calldata = array![]; //no need for arguments for a view function

            let to_address: ContractAddress = erc20_address.try_into().unwrap();

            let call = Call {
                to: to_address, selector: view, calldata: calldata.span()
            };

            let res = execute_single_call(call);

            let zero: Array<felt252> = array![0];
            let zero_span :  Span<felt252> = zero.span();
            
            assert!(res == zero_span);

            self.account.__validate__(calls)
        }

        fn is_valid_signature(
            self: @ContractState, hash: felt252, signature: Array<felt252>
        ) -> felt252 {
            1
        }
    }
}