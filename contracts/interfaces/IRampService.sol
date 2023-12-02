// SPDX-License-Identifier: UNLICENSED
pragma solidity >=0.8.4;

import "./IUniswapV2Router02.sol";

interface IRampService {
	event Sold(address token, uint256 amount, address receiver, string txid);

	event SwapAndSold(address token, uint256 amount, uint256[] amounts, address receiver, string txid);

	event Purchased(address token, uint256 amount, string txid);

	event SwapAndPurchased(address token, uint256 amount, uint256[] amounts, string txid);

	struct BuyRequest {
		address receiver;
		address token;
		uint256 amount;
		string txId;
	}

	struct BuyBySwapRequest {
		address receiver;
		IUniswapV2Router02 router;
		address[] path;
		uint256 amount;
		uint256 minAmountOut;
		string txId;
	}

	struct SellRequest {
		address token;
		uint256 amount;
		string txId;
	}

	struct SellBySwapRequest {
		IUniswapV2Router02 router;
		address[] path;
		uint256 amount;
		uint256 minAmountOut;
		string txId;
	}

    function buy(
		BuyRequest calldata request,
		uint8 v,
		bytes32 r,
		bytes32 s
	) external;

	function buyBySwap(
		BuyBySwapRequest calldata request,
		uint8 v,
		bytes32 r,
		bytes32 s
	) external;

	function sell(
		SellRequest calldata request,
		uint8 v,
		bytes32 r,
		bytes32 s
	) external payable;

	function sellBySwap(
		SellBySwapRequest calldata request,
		uint8 v,
		bytes32 r,
		bytes32 s
	) external payable;

	function buyGetPrice(
		IUniswapV2Router02 router,
		address[] calldata path,
		uint256 amount,
		bool exactIn
	) external returns (uint256[] memory);

	function sellGetPrice(
		IUniswapV2Router02 router,
		address[] calldata path,
		uint256 amount,
		bool exactIn
	) external returns (uint256[] memory);
}