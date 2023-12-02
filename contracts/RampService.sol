// SPDX-License-Identifier: UNLICENSED
pragma solidity >=0.8.4;

import "@openzeppelin/contracts/access/AccessControl.sol";
import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "@openzeppelin/contracts/security/ReentrancyGuard.sol";

import "./interfaces/IRampService.sol";

contract RampService is AccessControl, IRampService, ReentrancyGuard {

	bytes32 public constant OWNER_ROLE = keccak256("OWNER_ROLE");

    bytes32 public constant ADMIN_ROLE = keccak256("ADMIN_ROLE");

    /// @notice The EIP-712 typehash for the contract's domain
	bytes32 public constant DOMAIN_TYPE_HASH =
		keccak256("EIP712Domain(string name,uint256 chainId,address verifyingContract)");

	/// @notice The EIP-712 typehash for the buy struct used by contract
	bytes32 public constant BUY_TYPE_HASH =
		keccak256("Buy(address receiver,address token,uint amount,string txId)");

	/// @notice The EIP-712 typehash for the buyBySwap struct used by contract
	bytes32 public constant BUY_BY_SWAP_TYPE_HASH =
		keccak256("BuyBySwap(address receiver,address router,address[] path,uint amount,uint minAmountOut,string txId)");

	/// @notice The EIP-712 typehash for the sell struct used by contract
	bytes32 public constant SELL_TYPE_HASH =
		keccak256("Sell(address token,uint amount,string txId)");

	/// @notice The EIP-712 typehash for the sellBySwap struct used by contract
	bytes32 public constant SELL_BY_SWAP_TYPE_HASH =
		keccak256("SellBySwap(address router,address[] path,uint amount,uint minAmountOut,string txId)");

	mapping(string => mapping(address => uint256)) public buyTx;

	mapping(string => mapping(address => uint256)) public swapTx;

	mapping(string => mapping(address => uint256)) public sellTx;

	/// @notice A record of signers
	mapping(address => bool) public signers;
	/// @notice A record of supported assets
	mapping(address => bool) public supportedAssets;
	/// @notice A record of address book
	mapping(address => bool) public addressBook;

    bytes32 public domainSeparator;

    bool public serviceActive;

	uint256 public balance;

	constructor() {
		uint256 chainId;

		//solhint-disable-next-line no-inline-assembly
		assembly {
			chainId := chainid()
		}

        domainSeparator = keccak256(
			abi.encode(DOMAIN_TYPE_HASH, keccak256(bytes("ChainVerse|RampService")), chainId, address(this))
		);

		_setRoleAdmin(OWNER_ROLE, OWNER_ROLE);
		_setRoleAdmin(ADMIN_ROLE, OWNER_ROLE);

		_grantRole(OWNER_ROLE, msg.sender);
		_grantRole(ADMIN_ROLE, msg.sender);

		serviceActive = true;
	}
	
	modifier isActive {
        require(serviceActive, "RampService: Service is off");
        _;
    }

	function updateService() external onlyRole(OWNER_ROLE) {
		serviceActive = !serviceActive;
	}

	function updateAsset(address asset) public onlyRole(ADMIN_ROLE) {
		supportedAssets[asset] = !supportedAssets[asset];
	}

	function updateSigner(address signer) public onlyRole(OWNER_ROLE) {
		signers[signer] = !signers[signer];
	}

	function updateAddressBook(address _address) public onlyRole(OWNER_ROLE) {
		addressBook[_address] = !addressBook[_address];
	}

	function buy(
		BuyRequest calldata request,
        uint8 v,
		bytes32 r,
		bytes32 s
	) public override nonReentrant isActive {
		require(supportedAssets[request.token], "RampService: asset is not supported");
		require(buyTx[request.txId][request.token] == 0, "RampService: txId is existed");

		bytes32 structHash = keccak256(
			abi.encode(
				BUY_TYPE_HASH, 
				request.receiver, 
				request.token,
				request.amount, 
				keccak256(bytes(request.txId))
			)
		);

		address signatory = ecrecover(keccak256(abi.encodePacked("\x19\x01", domainSeparator, structHash)), v,r,s);
		require(signatory != address(0) && signers[signatory], "RampService: invalid signature");

		bool sent = false;
		if (request.token == address(0)) {
			require(balance >= request.amount, "RampService: asset is not enough");

            balance = balance - request.amount;
            // solhint-disable-next-line avoid-low-level-calls
            (sent, ) = payable(request.receiver).call{ value: request.amount }("");
		} else {
			require(
				IERC20(request.token).balanceOf(address(this)) >= request.amount,
				"RampService: asset is not enough"
			);
			
            sent = IERC20(request.token).transfer(request.receiver, request.amount);
		}

		require(sent, "RampService: Failed Processing");
        
        buyTx[request.txId][request.token] = request.amount;

		emit Sold(request.token, request.amount, request.receiver, request.txId);
	}

	function buyBySwap(
		BuyBySwapRequest calldata request,
		uint8 v,
		bytes32 r,
		bytes32 s
	) public override nonReentrant isActive {
		require(supportedAssets[request.path[request.path.length - 1]], "RampService: asset is not supported");
		require(swapTx[request.txId][request.path[request.path.length - 1]] == 0, "RampService: txId is existed");

		bytes32 structHash = keccak256(
				abi.encode(
					BUY_BY_SWAP_TYPE_HASH,
					request.receiver,
					request.router,
					keccak256(abi.encodePacked(request.path)),
					request.amount,
					request.minAmountOut,
					keccak256(bytes(request.txId))
				)
			);

		address signatory = ecrecover(keccak256(abi.encodePacked("\x19\x01", domainSeparator, structHash)), v,r,s);
		require(signatory != address(0) && signers[signatory], "RampService: invalid signature");
		
		bool sent = false;
		uint256[] memory amounts;

        require(IERC20(request.path[0]).approve(address(request.router), request.amount), "RampService: Failed approval");
		if (request.path[request.path.length - 1] == request.router.WETH()) {

            amounts = request.router.swapExactTokensForETH(
                request.amount,
                request.minAmountOut,
                request.path,
                request.receiver,
                block.timestamp + 15
				);
				sent = true;

		} else {
            
            amounts = request.router.swapExactTokensForTokens(
                request.amount,
                request.minAmountOut,
                request.path,
                request.receiver,
                block.timestamp + 15
				);
				sent = true;
		}

		require(sent, "RampService: Failed Processing");

        swapTx[request.txId][request.path[request.path.length - 1]] = request.amount;
        
		emit SwapAndSold(request.path[request.path.length - 1], request.amount, amounts, request.receiver, request.txId);
	}

	function sell(
		SellRequest calldata request,
		uint8 v,
		bytes32 r,
		bytes32 s
	) public payable override nonReentrant isActive {
		require(supportedAssets[request.token], "RampService: asset is not supported");
		require(sellTx[request.txId][request.token] == 0, "RampService: txId is existed");
		require(request.amount > 0, "RampService: amount is invalid");

		bytes32 structHash = keccak256(
				abi.encode(
					SELL_TYPE_HASH,
					request.token,
					request.amount,
					keccak256(bytes(request.txId))
				)
			);

		address signatory = ecrecover(keccak256(abi.encodePacked("\x19\x01", domainSeparator, structHash)), v,r,s);
		require(signatory != address(0) && signers[signatory], "RampService: invalid signature");

		if (request.token == address(0)) {
			require(msg.value >= request.amount, "RampService: amount is wrong");
			balance = balance + request.amount;
		} else {
			require(IERC20(request.token).transferFrom(msg.sender, address(this), request.amount), "RampService: Failed Transferring");
		}

		sellTx[request.txId][request.token] = request.amount;

		emit Purchased(request.token, request.amount, request.txId);
	}

    function sellBySwap(
		SellBySwapRequest calldata request,
		uint8 v,
		bytes32 r,
		bytes32 s
	) public payable override nonReentrant isActive {
		require(supportedAssets[request.path[0]], "RampService: asset is not supported");
		require(swapTx[request.txId][request.path[0]] == 0, "RampService: txId is existed");
		require(request.amount > 0, "RampService: amount is invalid");
        
		bytes32 structHash = keccak256(
				abi.encode(
					SELL_BY_SWAP_TYPE_HASH,
					request.router,
					keccak256(abi.encodePacked(request.path)),
					request.amount,
					request.minAmountOut,
					keccak256(bytes(request.txId))
				)
			);

		address signatory = ecrecover(keccak256(abi.encodePacked("\x19\x01", domainSeparator, structHash)), v,r,s);
		require(signatory != address(0) && signers[signatory], "RampService: invalid signature");

        bool received = false;
        uint256[] memory amounts;
		if (request.path[0] == request.router.WETH()) {

            require(msg.value >= request.amount, "RampService: amount is wrong");

            amounts = request.router.swapExactETHForTokens {value: msg.value} (
                request.minAmountOut,
                request.path,
                address(this),
                block.timestamp + 15
				);
				received = true;

		} else {

            require(IERC20(request.path[0]).transferFrom(msg.sender, address(this), request.amount), "RampService: Failed Transferring from caller");

            require(IERC20(request.path[0]).approve(address(request.router), request.amount), "RampService: Failed approval");

            amounts = request.router.swapExactTokensForTokens(
                request.amount,
                request.minAmountOut,
                request.path,
                address(this),
                block.timestamp + 15
				);
				received = true;
		}

        require(received, "RampService: Failed Processing");

		swapTx[request.txId][request.path[0]] = request.amount;

		emit SwapAndPurchased(request.path[0], request.amount, amounts, request.txId);
	}

	function buyGetPrice(
		IUniswapV2Router02 router,
		address[] calldata path,
		uint256 amount,
		bool exactIn
	) public view returns (uint256[] memory amounts) {
		require(supportedAssets[path[path.length - 1]], "RampService: asset is not supported");
		
		if (exactIn) {
			return router.getAmountsOut(amount, path);
		}
		else {
			return router.getAmountsIn(amount, path);
		}
	}

    function sellGetPrice(
		IUniswapV2Router02 router,
		address[] calldata path,
		uint256 amount,
		bool exactIn
	) public view returns (uint256[] memory amounts) {
		require(supportedAssets[path[0]], "RampService: asset is not supported");

		if (exactIn) {
			return router.getAmountsOut(amount, path);
		}
		else {
			return router.getAmountsIn(amount, path);
		}
	}

	function approveRouter(
		address token,
		address router,
		uint256 amount
	) public onlyRole(ADMIN_ROLE) {
		//require(supportedAssets[token], "RampService: asset is not supported");
		require(router != address(0), "RampService: wrong router");

		IERC20(token).approve(router, amount);
	}

	function forceTransfer(
		address token,
		uint256 amount,
		address receiver
	) public onlyRole(OWNER_ROLE) returns (bool) {
		require(receiver != address(0), "RampService: invalid query");
		require(addressBook[receiver], "RampService: address not in addressBook");
		
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
}