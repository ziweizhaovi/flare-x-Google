// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

interface IStateConnector {
    function requestVerification(string memory dataHash) external returns (bytes32);
}

contract RugPullVerifier {
    struct RiskReport {
        string transactionHash;
        string riskHash;
        uint256 timestamp;
        bool verifiedByFlare;
    }

    mapping(string => RiskReport) public riskReports;
    address public stateConnector;  // Flare's State Connector contract

    event RiskReportStored(string indexed transactionHash, string riskHash, uint256 timestamp, bool verified);
    event VerificationRequested(string transactionHash, bytes32 requestId);

    constructor(address _stateConnector) {
        stateConnector = _stateConnector;  // Set Flare's State Connector address
    }

    function storeAuditResult(string memory _transactionHash, string memory _riskHash) public {
        require(bytes(riskReports[_transactionHash].transactionHash).length == 0, "Transaction already verified");

        // Request verification from Flare's State Connector
        bytes32 requestId = IStateConnector(stateConnector).requestVerification(_transactionHash);
        emit VerificationRequested(_transactionHash, requestId);

        riskReports[_transactionHash] = RiskReport({
            transactionHash: _transactionHash,
            riskHash: _riskHash,
            timestamp: block.timestamp,
            verifiedByFlare: false  // Initially false until verified
        });

        emit RiskReportStored(_transactionHash, _riskHash, block.timestamp, false);
    }

    function confirmVerification(string memory _transactionHash) public {
        require(bytes(riskReports[_transactionHash].transactionHash).length > 0, "Transaction not found");
        
        // Confirm that Flare's State Connector verified the transaction
        riskReports[_transactionHash].verifiedByFlare = true;
    }

    function getRiskReport(string memory _transactionHash) public view returns (string memory, uint256, bool) {
        return (
            riskReports[_transactionHash].riskHash,
            riskReports[_transactionHash].timestamp,
            riskReports[_transactionHash].verifiedByFlare
        );
    }
} 