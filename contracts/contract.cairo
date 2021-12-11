%lang starknet
%builtins pedersen range_check ecdsa

from starkware.cairo.common.cairo_builtins import HashBuiltin, SignatureBuiltin
from starkware.cairo.common.hash import hash2
from starkware.cairo.common.signature import verify_ecdsa_signature
from starkware.starknet.common.syscalls import get_tx_signature
from starkware.starknet.common.syscalls import get_caller_address


@storage_var
func _balance(user : felt) -> (res : felt):
end


@storage_var
func _owner() -> (res : felt):
end

@constructor
func constructor{
        syscall_ptr : felt*,
        pedersen_ptr : HashBuiltin*,
        range_check_ptr
    }(owner_address : felt):
    _owner.write(value=owner_address)
    return ()
end


@external
func increase_balance{
        syscall_ptr : felt*,
        pedersen_ptr : HashBuiltin*,
        range_check_ptr,
        ecdsa_ptr : SignatureBuiltin*
    }(amount : felt):
    let (user) = get_caller_address()
    let (res) = _balance.read(user)
    _balance.write(user, res + amount)
    return ()
end


@view
func get_balance{
            syscall_ptr : felt*,
            pedersen_ptr : HashBuiltin*,
            range_check_ptr
        }(user : felt) -> (res : felt):
    let (res) = _balance.read(user)
    return (res)
end

@view
func only_owner{
        syscall_ptr : felt*, 
        pedersen_ptr : HashBuiltin*,
        range_check_ptr
    }():
    let (owner) = _owner.read()
    let (caller) = get_caller_address()
    assert owner = caller
    return ()
end


@view
func get_owner{
        syscall_ptr : felt*,
        pedersen_ptr : HashBuiltin*,
        range_check_ptr
    }() -> (res : felt):
    let (res) = _owner.read()
    return (res)
end


@external
func set_owner{
        syscall_ptr : felt*,
        pedersen_ptr : HashBuiltin*,
        range_check_ptr,
        ecdsa_ptr : SignatureBuiltin*
    }(new_owner : felt):
    only_owner()
    _owner.write(new_owner)
    return ()
end
