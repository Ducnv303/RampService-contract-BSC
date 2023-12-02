// SPDX-License-Identifier: UNLICENSED
pragma solidity >=0.8.4;

import "@openzeppelin/contracts/access/AccessControl.sol";
import "@openzeppelin/contracts/token/ERC20/IERC20.sol";

contract RampManager is AccessControl {
	bytes32 public constant OWNER_ROLE = keccak256("OWNER_ROLE");

	/// @notice The EIP-712 typehash for the contract's domain
	bytes32 public constant DOMAIN_TYPE_HASH =
		keccak256("EIP712Domain(string name,uint256 chainId,address verifyingContract)");

	mapping(address => bool) public signers;

	bytes32 public domainSeparator;

	uint256 public balance;
	
	constructor() {
		uint256 chainId;

		domainSeparator = keccak256(
			abi.encode(DOMAIN_TYPE_HASH, keccak256(bytes("ChainVerse|RampManager")), chainId, address(this))
		);

		//solhint-disable-next-line no-inline-assembly
		assembly {
			chainId := chainid()
		}

		_setRoleAdmin(OWNER_ROLE, OWNER_ROLE);
		_setupRole(OWNER_ROLE, msg.sender);

	}

	function withdraw(
		address token,
		uint256 amount,
		address receiver
	) public onlyRole(OWNER_ROLE) returns (bool) {
		require(receiver != address(0), "RampService: invalid query");
		bool sent = false;
		if (token == address(0)) {
			require(balance >= amount, "RampService: asset is not enough");
			balance = balance - amount;
			// solhint-disable-next-line avoid-low-level-calls
			(sent, ) = payable(receiver).call{ value: amount }("");
		} else {
			require(IERC20(token).balanceOf(address(this)) >= amount, "RampService: Token is not enough");
			sent = IERC20(token).transfer(receiver, amount);
		}

		return sent;
	}

	receive() external payable {
		balance += msg.value;
	}

    // event NewRampService(address indexed rampService);

    // function createRampService() external {
    //     RampService newContract = new RampService();
    //     emit NewRampService(address(newContract));
    // }
}

