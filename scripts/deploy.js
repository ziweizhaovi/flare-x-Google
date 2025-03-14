const hre = require("hardhat");

async function main() {
    const RugPullVerifier = await hre.ethers.getContractFactory("RugPullVerifier");
    const contract = await RugPullVerifier.deploy();

    await contract.waitForDeployment(); // Fix for Ethers v6+

    console.log("✅ Contract Deployed at:", await contract.getAddress());
}

main()
    .then(() => process.exit(0))
    .catch((error) => {
        console.error(error);
        process.exit(1);
    });

