const { expect } = require("chai");
const { ethers } = require("hardhat");

describe("DeFiAuditReport", function () {
  let defiAuditReport;
  let owner;
  let addr1;

  beforeEach(async function () {
    [owner, addr1] = await ethers.getSigners();
    
    const DeFiAuditReport = await ethers.getContractFactory("DeFiAuditReport");
    defiAuditReport = await DeFiAuditReport.deploy();
  });

  describe("Deployment", function () {
    it("Should set the right owner", async function () {
      expect(await defiAuditReport.owner()).to.equal(owner.address);
    });
  });

  describe("Reports", function () {
    it("Should add a new report", async function () {
      await defiAuditReport.addReport(
        "WETH",
        "USDC",
        -2000, // -20%
        "High risk detected"
      );

      const report = await defiAuditReport.getReport(0);
      expect(report.token0).to.equal("WETH");
      expect(report.token1).to.equal("USDC");
      expect(report.changePercentage).to.equal(-2000);
      expect(report.aiAnalysis).to.equal("High risk detected");
    });

    it("Should fail if non-owner tries to add report", async function () {
      await expect(
        defiAuditReport.connect(addr1).addReport(
          "WETH",
          "USDC",
          -2000,
          "High risk detected"
        )
      ).to.be.revertedWithCustomError(defiAuditReport, "OwnableUnauthorizedAccount");
    });
  });
}); 