const { expect } = require("chai");
const { ethers } = require("hardhat");

describe("RugPullVerifier", function () {
  let rugPullVerifier;
  let owner;
  let addr1;
  let mockStateConnector;

  beforeEach(async function () {
    [owner, addr1] = await ethers.getSigners();
    
    // Deploy a mock StateConnector first
    const MockStateConnector = await ethers.getContractFactory("MockStateConnector");
    mockStateConnector = await MockStateConnector.deploy();
    
    const RugPullVerifier = await ethers.getContractFactory("RugPullVerifier");
    rugPullVerifier = await RugPullVerifier.deploy(await mockStateConnector.getAddress());
  });

  describe("Risk Reports", function () {
    const testTxHash = "0x1234567890abcdef";
    const testRiskHash = "QmTest123";

    it("Should store a new risk report", async function () {
      await rugPullVerifier.storeAuditResult(testTxHash, testRiskHash);
      
      const report = await rugPullVerifier.getRiskReport(testTxHash);
      expect(report[0]).to.equal(testRiskHash);
      expect(report[2]).to.equal(false); // verifiedByFlare should be false initially
    });

    it("Should not allow duplicate transaction reports", async function () {
      await rugPullVerifier.storeAuditResult(testTxHash, testRiskHash);
      
      await expect(
        rugPullVerifier.storeAuditResult(testTxHash, testRiskHash)
      ).to.be.revertedWith("Transaction already verified");
    });
  });
});