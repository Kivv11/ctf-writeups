# Coduct

[Español](README.md) | [English](README.en.md)

**Challenge 6 · PWN · Difficulty: Medium**

## Challenge

> Coduct Bank has recently launched a new internal banking terminal to test its next-generation transaction system. The application allows employees to deposit and withdraw virtual coins before redeeming rewards from a secure vault. According to the developers, only accounts holding at least one million coins can access the vault and retrieve confidential company assets.
>
> During a routine security assessment, your team noticed that the system stores balances as unsigned 32-bit integers. While reviewing the transaction logic, you discovered that withdrawals are processed before any validation takes place. A seemingly harmless arithmetic error could cause balances to underflow and reach enormous values. Your objective is to exploit this flaw, unlock the vault, and retrieve the protected flag.

## Flag
```
1nt3g3r_und3rfl0w_g0n3_n1c3
```

## Solution

The terminal is accessed using Netcat:
```
nc challenges2.hackrocks.com 6717
```

Upon establishing the connection, the following menu appears:
```markdown
1. Check Balance
2. Deposit Coins
3. Withdraw Coins
4. Check Vault
5. Show Challenge Info
0. Exit
```

Option `5` (**Show Challenge Info**) indicates that the initial balance is **100 coins**, that `uint32` is used, and that a validation check is missing before subtraction. It also provides a hint: what happens when calculating `0 - 1` as `uint32_t`?

The balance is checked using option `1` (**Check Balance**), and option `3` (**Withdraw Coins**) is selected to withdraw one coin more than the available balance. The program performs the subtraction without preventing the balance from dropping below zero, causing an **Integer Underflow**.

Starting with 100 coins, withdrawing 101 results in `100 - 101 = -1`, which wraps around to `4294967295` in a `uint32`.
```yaml
coduct-bank > 3
Withdraw amount: 101

[+] Withdrew 101 coins. Balance: 4294967295
```

With the balance exceeding the required one million coins, option `4` (**Check Vault**) is selected:
```yaml
coduct-bank > 4

[!!!] VAULT UNLOCKED
Balance: 4,294,967,295 coins

[!!!] FLAG: 1nt3g3r_und3rfl0w_g0n3_n1c3
```
