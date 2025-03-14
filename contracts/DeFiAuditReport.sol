// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/access/Ownable.sol";

contract DeFiAuditReport is Ownable {
    struct AuditReport {
        string token0;
        string token1;
        int256 changePercentage;
        string aiAnalysis;
        uint256 timestamp;
    }

    AuditReport[] public reports;
    
    event ReportAdded(
        uint256 indexed reportId,
        string token0,
        string token1,
        int256 changePercentage,
        uint256 timestamp
    );

    constructor() Ownable(msg.sender) {}

    function addReport(
        string memory token0,
        string memory token1,
        int256 changePercentage,
        string memory aiAnalysis
    ) public onlyOwner {
        reports.push(AuditReport({
            token0: token0,
            token1: token1,
            changePercentage: changePercentage,
            aiAnalysis: aiAnalysis,
            timestamp: block.timestamp
        }));

        emit ReportAdded(
            reports.length - 1,
            token0,
            token1,
            changePercentage,
            block.timestamp
        );
    }

    function getReport(uint256 reportId) public view returns (AuditReport memory) {
        require(reportId < reports.length, "Report does not exist");
        return reports[reportId];
    }

    function getReportCount() public view returns (uint256) {
        return reports.length;
    }
} 