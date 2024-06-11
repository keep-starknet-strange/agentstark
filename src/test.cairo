use openzeppelin::account::AccountComponent::{InternalTrait, SRC6CamelOnlyImpl};
use openzeppelin::account::AccountComponent::{OwnerAdded, OwnerRemoved};
use openzeppelin::account::AccountComponent::{PublicKeyCamelImpl, PublicKeyImpl};
use openzeppelin::account::AccountComponent;
use openzeppelin::account::interface::{AccountABIDispatcherTrait, AccountABIDispatcher};
use openzeppelin::account::interface::{ISRC6, ISRC6_ID};
use openzeppelin::introspection::interface::{ISRC5, ISRC5_ID};


use agentstark::account_mock::DualCaseAccountMock;
use agentstark::erc20_mock::DualCaseERC20Mock;
//use openzeppelin::tests::mocks::account_mocks::DualCaseAccountMock;
//use openzeppelin::tests::mocks::erc20_mocks::DualCaseERC20Mock;
use openzeppelin::tests::utils::constants::{
    NAME, SYMBOL, PUBKEY, NEW_PUBKEY, SALT, ZERO, QUERY_OFFSET, QUERY_VERSION,
    MIN_TRANSACTION_VERSION
};
use openzeppelin::tests::utils;
use openzeppelin::token::erc20::interface::{IERC20DispatcherTrait, IERC20Dispatcher};
use openzeppelin::utils::selectors;
use openzeppelin::utils::serde::SerializedAppend;
use starknet::ContractAddress;
use starknet::account::Call;
use starknet::contract_address_const;
use starknet::testing;


#[derive(Drop)]
struct SignedTransactionData {
    private_key: felt252,
    public_key: felt252,
    transaction_hash: felt252,
    r: felt252,
    s: felt252
}

fn SIGNED_TX_DATA() -> SignedTransactionData {
    SignedTransactionData {
        private_key: 1234,
        public_key: 0x1f3c942d7f492a37608cde0d77b884a5aa9e11d2919225968557370ddb5a5aa,
        transaction_hash: 0x601d3d2e265c10ff645e1554c435e72ce6721f0ba5fc96f0c650bfc6231191a,
        r: 0x6c8be1fb0fb5c730fbd7abaecbed9d980376ff2e660dfcd157e158d2b026891,
        s: 0x76b4669998eb933f44a59eace12b41328ab975ceafddf92602b21eb23e22e35
    }
}

//
// Constants
//



fn CLASS_HASH() -> felt252 {
    0
}

fn ACCOUNT_ADDRESS() -> ContractAddress {
    contract_address_const::<0x111111>()
}

//
// Setup
//

type ComponentState = AccountComponent::ComponentState<DualCaseAccountMock::ContractState>;

fn CONTRACT_STATE() -> DualCaseAccountMock::ContractState {
    DualCaseAccountMock::contract_state_for_testing()
}

fn setup_dispatcher(data: Option<@SignedTransactionData>) -> AccountABIDispatcher {
    testing::set_version(MIN_TRANSACTION_VERSION);

    let mut calldata = array![];
    if data.is_some() {
        let data = data.unwrap();
        testing::set_signature(array![*data.r, *data.s].span());
        testing::set_transaction_hash(*data.transaction_hash);

        calldata.append(*data.public_key);
    } else {
        calldata.append(PUBKEY);
    }
    let address = utils::deploy(CLASS_HASH(), calldata);
    AccountABIDispatcher { contract_address: address }
}

fn deploy_erc20(recipient: ContractAddress, initial_supply: u256) -> IERC20Dispatcher {
    let mut calldata = array![];

    calldata.append_serde(NAME());
    calldata.append_serde(SYMBOL());
    calldata.append_serde(initial_supply);
    calldata.append_serde(recipient);

    let address = utils::deploy(CLASS_HASH(), calldata);
    IERC20Dispatcher { contract_address: address }
}





#[test]
fn test_validate_declare() {
    let account = setup_dispatcher(Option::Some(@SIGNED_TX_DATA()));

    // `__validate_declare__` does not directly use the class_hash argument. Its
    // value is already integrated in the tx hash. The class_hash argument in this
    // testing context is decoupled from the signature and has no effect on the test.
    let is_valid = account.__validate_declare__(CLASS_HASH());
    assert_eq!(is_valid, starknet::VALIDATED);
}



fn test_execute_with_version(version: Option<felt252>) {
    let data = SIGNED_TX_DATA();
    let account = setup_dispatcher(Option::Some(@data));
    let erc20 = deploy_erc20(account.contract_address, 1000);
    let recipient = contract_address_const::<0x123>();

    // Craft call and add to calls array
    let mut calldata = array![];
    let amount: u256 = 200;
    calldata.append_serde(recipient);
    calldata.append_serde(amount);
    let call = Call {
        to: erc20.contract_address, selector: selectors::transfer, calldata: calldata.span()
    };
    let mut calls = array![];
    calls.append(call);

    // Handle version for test
    if version.is_some() {
        testing::set_version(version.unwrap());
    }

    // Execute
    let ret = account.__execute__(calls);

    // Assert that the transfer was successful
    assert_eq!(erc20.balance_of(account.contract_address), 800, "Should have remainder");
    assert_eq!(erc20.balance_of(recipient), amount, "Should have transferred");

    // Test return value
    let mut call_serialized_retval = *ret.at(0);
    let call_retval = Serde::<bool>::deserialize(ref call_serialized_retval);
    assert!(call_retval.unwrap());
}






#[test]
fn test_validate() {
    let calls = array![];
    let account = setup_dispatcher(Option::Some(@SIGNED_TX_DATA()));

    let is_valid = account.__validate__(calls);
    assert_eq!(is_valid, starknet::VALIDATED);
}





//
// Helpers
//

fn assert_event_owner_removed(contract: ContractAddress, removed_owner_guid: felt252) {
    let event = utils::pop_log::<AccountComponent::Event>(contract).unwrap();
    let expected = AccountComponent::Event::OwnerRemoved(OwnerRemoved { removed_owner_guid });
    assert!(event == expected);

    // Check indexed keys
    let mut indexed_keys = array![];
    indexed_keys.append_serde(selector!("OwnerRemoved"));
    indexed_keys.append_serde(removed_owner_guid);
    utils::assert_indexed_keys(event, indexed_keys.span());
}

fn assert_event_owner_added(contract: ContractAddress, new_owner_guid: felt252) {
    let event = utils::pop_log::<AccountComponent::Event>(contract).unwrap();
    let expected = AccountComponent::Event::OwnerAdded(OwnerAdded { new_owner_guid });
    assert!(event == expected);

    // Check indexed keys
    let mut indexed_keys = array![];
    indexed_keys.append_serde(selector!("OwnerAdded"));
    indexed_keys.append_serde(new_owner_guid);
    utils::assert_indexed_keys(event, indexed_keys.span());
}

fn assert_only_event_owner_added(contract: ContractAddress, new_owner_guid: felt252) {
    assert_event_owner_added(contract, new_owner_guid);
    utils::assert_no_events_left(contract);
}
