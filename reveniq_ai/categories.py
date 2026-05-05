"""
Memo-text categorisation rules for ReveniQ AI - Initial Goal.
Maps MEMO_TEXT content to dispute categories (up to 100 categories).
Digital COE Gen AI Team
"""

import re
from typing import Optional, Tuple

# Pre-compiled regexes (used in _normalize_text) to avoid recompiling per row
_RE_NL = re.compile(r"[\r\n\t]+")
_RE_PUNCT = re.compile(r"[\.,;:!?\-_'\"\/()\[\]]+")
_RE_SPACES = re.compile(r"\s+")

# Flat category structure: (Category Name, Keywords, Base Confidence)
# Base confidence: 0.9 = high, 0.8 = medium-high, 0.7 = medium, 0.6 = low-medium
CATEGORY_RULES = [
    # Payment & Allocation (1-10)
    ("Payment Allocation / POP", [
        "allocate payment", "allocation", "payment not reflected", "payment has not reflected",
        "proof of payment", " pop ", "attached proof", "payment not yet reflected",
        "allocate the payment", "kindly assist with allocating", "allocating the payment",
        "please allocate", "assist with allocating", "customer paid", "payment at pick n pay",
        "made a payment", "eft payment", "payment is being paid", "pop on the attachment",
        "pop is attached", "bank statement", "payment not client", "easypay slip",
        "slip attached as proof", "assist with payment", "online payment not reflecting",
        "payment not reflecting on fa", "payment not on fa", "not reflecting on fa",
        "billing template", "payment allocation", "allocated to", "allocation of payment",
        "payment proof", "paid on", "allocation request", "unallocated payment",
        "paid but still not showing", "paid in dec but allocated", "only one reflecting",
        "sent to petro to trace", "paymnt", "cist made", "two paymnt",
    ], 0.9),
    ("Payment Extension Request", [
        "more time to pay", "extra time to pay", "extension requested", "need extension",
        "request extension", "extend the payment", "delay payment", "postpone payment",
        "payment extension", "extension of payment", "pay later", "extension is 15 days",
        "extend payment", "payment delay", "defer payment", "extend due date",
    ], 0.85),
    ("Payment Method Update", [
        "change payment", "update payment", "payment method", "banking details",
        "change banking", "update banking", "new bank account", "change account",
        "bank details", "account number", "branch code", "update account number",
    ], 0.85),
    ("Failed Debit / Bank Charge", [
        "bounced", "couldn't debit", "could not debit", "debit order did not go through",
        "debit was not successful", "disputing the charges", "dispute the charges",
        "wasn't his fault that telkom", "had money in the account", "had money in their account",
        "not his fault that the debit", "money was not debited on the debit date",
        "irregular debit orders", "irregular debit", "does not reflect on her fa",
        "does not reflect on his fa", "disputes it at the bank",
        "debit failed", "debit bounce", "unsuccessful debit", "debit not gone through",
        "debit order failed", "returned debit", "rejected debit", "insufficient funds",
    ], 0.9),
    ("Payment Processing Error", [
        "payment error", "payment mistake", "incorrect payment", "wrong payment",
        "payment issue", "payment problem", "payment failed", "payment declined",
        "payment not processed", "processing error", "failed to process",
    ], 0.8),
    ("Payment Refund Processing", [
        "refund processing", "process refund",         "refund payment", "refund transaction", "refund to be processed", "refund pending",
    ], 0.8),
    ("Payment Discrepancy", [
        "payment discrepancy", "payment difference", "payment mismatch", "payment incorrect",
        "amount discrepancy", "wrong amount paid", "overpayment", "underpayment",
    ], 0.75),
    ("Payment Plan Request", [
        "payment plan", "installment plan",         "payment arrangement", "payment schedule", "pay in installments", "arrangement to pay",
        "ptp", "promise to pay", "glory ptp",
    ], 0.8),
    ("Payment History Query", [
        "payment history", "payment record", "payment statement", "payment log",
    ], 0.7),
    ("Payment Gateway Issue", [
        "payment gateway", "gateway error", "payment system", "online payment issue",
    ], 0.75),
    
    # Refunds & Credits (11-25)
    ("Refund Request", [
        "refund case", "refund enquiry", "requested for a refund", "requesting his deposit back",
        "returned back to his", "returned back to her", "return to his personal account",
        "return to her personal account", "to be returned back", "returned back to his/her",
        "refund of r", "assist with refund", "kindly assist with refund",
        "customer over paid", "over paid account", "requesting for refund", "request refund",
        "refund must be paid into", "banking details the refund", "credit vet", "deposit back",
        "refund request", "want refund", "need refund", "refund back", "money back",
        "return the money", "refund amount", "get refund", "requesting refund",
    ], 0.9),
    ("General Credit Request", [
        "creditting", "credit the customer", "credit the customers account",
        "assist in creditting", "please credit", "kindly credit", "to be credited",
        "amount to be credited", "please assist with crediting", "waived off",
        "charges waived", "credit her account", "credit his account",
        "not given the second credit", "not given the credit",
        "credit account", "apply credit", "give credit", "credit note", "adjustment credit",
    ], 0.85),
    ("Credit Limit Increase", [
        "credit limit", "credit limt", "over the limit", "increase the credit",
        "credit limit is", "credit limit in", "increase his credit", "increase her credit",
        "increase credit limit", "increase customer credit", "please increase credit",
        "credit limit to be increased", "credit limit is not being adjusted",
        "amount due is more than the credit limit", "please increase credit limit",
        "increase credit above", "increased from", "increase from", "credit limit r",
        "customer cannot make calls", "account in collection with r0",
        "please increase the credit limt", "increase the credit limit",
        "currently on zero", "credit limit its currently", "increase spending limit",
        "please increase spending limit", "credite limit", "zero and cost the customers account",
        "increase limit", "spend limit increase", "limit increase",
    ], 0.9),
    ("Credit Adjustment Request", [
        "credit adjustment", "adjust credit", "credit correction", "credit modification",
    ], 0.8),
    ("Credit Balance Query", [
        "credit balance", "available credit", "credit available", "credit remaining",
    ], 0.75),
    ("Credit Limit Decrease Request", [
        "decrease credit limit", "lower credit limit", "reduce credit limit",
    ], 0.8),
    ("Credit Application", [
        "apply for credit", "credit application", "request credit", "credit approval",
    ], 0.75),
    ("Credit Terms Dispute", [
        "credit terms", "credit conditions", "credit agreement", "credit policy",
    ], 0.7),
    ("Credit Score Query", [
        "credit score", "credit rating", "credit check", "credit assessment",
    ], 0.7),
    ("Credit Facility Request", [
        "credit facility", "credit line", "credit access", "credit availability",
    ], 0.75),
    ("Credit Interest Dispute", [
        "credit interest", "interest on credit", "credit charge", "credit fee",
    ], 0.75),
    ("Credit Reversal Request", [
        "reverse credit", "credit reversal", "undo credit", "cancel credit",
    ], 0.8),
    ("Credit Transfer Request", [
        "transfer credit", "credit transfer", "move credit", "credit move",
    ], 0.75),
    ("Credit Expiry Query", [
        "credit expiry", "credit expiration", "credit valid", "credit validity",
    ], 0.7),
    ("Credit Limit Review", [
        "review credit limit", "credit limit review", "reassess credit", "credit reassessment",
    ], 0.75),
    ("Credit Terms Negotiation", [
        "negotiate credit", "credit negotiation", "credit terms discussion",
    ], 0.7),
    
    # Account Management (26-40)
    ("Account Suspension / Lift Suspension", [
        "suspention to be lifted", "suspension to be lifted", "lift the susp",
        "suspended for the whole week", "account is suspended", "account was suspended",
        "still suspended", "unsuspended", "unsuspend", "please assist unsuspended",
        "assist unsuspended", "account is suspended due to credit", "suspended due to",
        "back outs keep getting her account suspended", "reconnecting customer",
        "reconnect customer", "debit orders has not been going off",
        "reactivate line", "reactivate customer", "reactivate the", "reactivate client",
        "telkom did not deduct", "did not deduct first two", "debit date is every 25th",
        "debit date 25th", "debited everything on 15 december", "please assist with unsuspention",
    ], 0.9),
    ("Account Balance / Statement Query", [
        "balance", "statement", "account balance", "outstanding balance",
        "amount due", "what is owed", "how much", "account query",
        "balance enquiry", "statement request", "account statement",
        "outstanding", "balance due", "current balance", "amount owing", "owed",
    ], 0.75),
    ("FA / Account Update Request", [
        "update customer fa", "update fa", "please update", "kindly update customer fa",
        "customer is complaing that telkom debited", "there is credit please update",
        "update fa", "update financial account", "fa update",
    ], 0.8),
    ("Paid-up / Delisting Letter", [
        "delisting", "delisting request", "paid up letter", "paid-up letter",
        "paid  up letter", "request for paid up letter", "customer is done paying",
        "requesting a paid up letter",
    ], 0.85),
    ("Account Closure Request", [
        "close account", "account closure", "terminate account", "cancel account",
    ], 0.85),
    ("Account Reactivation", [
        "reactivate account", "reopen account", "restore account", "activate account",
    ], 0.85),
    ("Account Status Query", [
        "account status", "account state", "account condition", "account information",
    ], 0.75),
    ("Account Details Update", [
        "update account", "change account details", "modify account", "account modification",
    ], 0.8),
    ("Account Verification", [
        "verify account", "account verification", "confirm account", "validate account",
    ], 0.75),
    ("Account Access Issue", [
        "cannot access account", "account access", "login issue", "account login",
    ], 0.8),
    ("Account Security", [
        "account security", "security issue", "account breach", "account hacked",
    ], 0.85),
    ("Account Transfer", [
        "transfer account", "account transfer", "move account", "account migration",
    ], 0.75),
    ("Account Merge Request", [
        "merge account", "combine account", "consolidate account", "unify account",
    ], 0.75),
    ("Account Split Request", [
        "split account", "separate account", "divide account", "account division",
    ], 0.75),
    ("Account History Query", [
        "account history", "account record", "account log", "account timeline",
    ], 0.7),
    
    # Billing Disputes (41-60)
    ("Duplicate or Incorrect Billing", [
        "billed for 2 services", "being billed for", "duplicate", "incorrect charge",
        "did not apply", "not applied for", "wrong charge",         "billing dispute", "billed incorrectly", "incorrect billing", "wrong bill",
        "two services", "double debit", "debited again on the", "taken off twice",
        "double debit", "made a manually payment", "debited etc",
        "billed twice", "billed 2,", "billed  2,",
    ], 0.9),
    ("Events Billing", [
        "events billing", "event billing",
    ], 0.85),
    ("Billing Period / Date Dispute", [
        "billing period", "billing date", "invoice date", "charge date",
        "wrong date", "incorrect date", "date issue", "period issue",
        "bill date", "invoice period", "billing cycle date",
        "date is incorrect on system", "date is incorrect",
    ], 0.8),
    # Higher confidence (0.95) so rejection-fee memos win over "Failed Debit" when both match
    ("Rejection Fee Dispute", [
        "rejection fee", "rejection fees", "rejection of a rejection", "dispute the rejection",
        "disputing the rejection", "dispute the rejection fee", "disputing the rejection fee",
        "rejection fee of r", "rejection fee as",
        "desputing the rejection", "debit date was wrong",
        "would like to disputes rejection", "charged rejection fee", "rejection fee charged",
        "customer dispute the rejection", "dispute the rejection fee r20", "rejection fee r202",
        "charged for debit order rejection", "debit order rejection", "r202.70 rejection",
        "dispute r202.70 as rejection", "dispute the r202.70", "as rejection",
        "charged r202.70 for payment rejection", "account has been charged r202.70",
        "dispute the rejection fee r202", "rejectionfee", "rejecection", "rejecection+late fee",
        "r202.70", "202.70", "penalty fee r202.70",
        "back out", "backout", "back outs",
    ], 0.95),
    ("Late Payment / Interest Dispute", [
        "late payment interest", "late payment interest fee", "interest fee",
        "why her bill is so high",
        "payment being processed late", "processed late", "query on dhet",
        "charged late payment fee", "late payment fee", "customer was charged late payment",
        "late paymnet", "late payemnt", "late payemnt fee",
    ], 0.85),
    ("Billing Error Correction", [
        "billing error", "billing mistake", "correct billing", "fix billing",
    ], 0.85),
    ("Invoice Dispute", [
        "invoice dispute", "invoice issue", "invoice problem", "invoice incorrect",
    ], 0.8),
    ("Billing Cycle Dispute", [
        "billing cycle", "billing frequency", "billing schedule", "billing interval",
    ], 0.75),
    ("Tax Amount Dispute", [
        "tax dispute", "tax amount", "tax incorrect", "tax error", "vat dispute",
        "vat amount", "vat incorrect", "taxation", "vat issue",
    ], 0.8),
    ("Billing Address Update", [
        "billing address", "update billing address", "change billing address",
    ], 0.75),
    ("Billing Method Change", [
        "billing method", "change billing", "billing preference", "billing option",
    ], 0.75),
    ("Billing Notification Issue", [
        "billing notification", "bill notification", "invoice notification", "billing alert",
    ], 0.7),
    ("Billing Discrepancy", [
        "billing discrepancy", "bill difference", "invoice difference", "billing mismatch",
    ], 0.8),
    ("Billing Query", [
        "billing query", "bill question", "invoice query", "billing question",
    ], 0.7),
    ("Billing Statement Request", [
        "billing statement", "bill statement", "invoice statement", "statement request",
    ], 0.75),
    ("Billing Dispute Resolution", [
        "resolve billing", "billing resolution", "settle billing", "billing settlement",
    ], 0.75),
    ("Billing Credit Request", [
        "billing credit", "bill credit", "invoice credit", "billing adjustment",
    ], 0.8),
    ("Billing Refund Request", [
        "billing refund", "bill refund", "invoice refund", "billing reimbursement",
    ], 0.8),
    ("Billing Payment Plan", [
        "billing plan", "bill plan", "payment plan for bill", "billing installment",
    ], 0.75),
    ("Billing Dispute Escalation", [
        "escalate billing", "billing escalation", "billing complaint", "billing issue escalate",
    ], 0.75),
    
    # Service & Contract Management (61-75)
    ("Cancellation or 30-Day Notice", [
        "30 day notice", "30-day notice", "contract was not cancelled", "final invoice",
        "contract not cancelled", "cancellation", "cancel the contract", "cancel below sub",
        "cancellation request", "cancellation was done", "cancelled in huawei",
        "customer requested cease", "cease order", "ceasing the number",
        "submitted a cancellation", "cancelaltion", "only one number was cancelled",
        "did not give me any proof that it was cancelled", "no usage on the sim",
        "cancelled their prime", "prime video", "getting charged for it",
        "cancel service", "cancel contract", "terminate", "cease", "cancelled",
        "not cancelled", "still being charged after cancel", "cancel the",
        "cancel with suspension", "cpa cancallation", "cpa cancellation",
    ], 0.9),
    ("Service Activation / Deactivation", [
        "activate", "activation", "deactivate", "deactivation", "service not working",
        "cannot connect", "connection issue", "network problem", "service issue",
        "line not working", "internet not working", "cannot access",
        "service not active", "activate service", "deactivate service", "line not active",
    ], 0.8),
    ("Service Upgrade / Downgrade", [
        "upgrade", "downgrade", "change plan", "plan change", "service change",
        "package change", "change package", "upgrade service", "downgrade service",
    ], 0.8),
    ("Service Outage / Connectivity", [
        "no signal", "cannot make calls", "cannot receive calls", "network down",
        "service outage", "connection problem", "internet down", "no internet",
        "line dead", "phone not working", "cannot connect", "network issue",
    ], 0.8),
    ("Data / Usage Disputes", [
        "data usage", "data charges", "unexpected data", "data not working",
        "slow internet", "speed issue", "bandwidth", "data cap",
    ], 0.75),
    ("Contract Terms Dispute", [
        "contract terms", "agreement issue", "contract dispute", "terms and conditions",
        "contract violation", "breach of contract", "contractual issue",
    ], 0.75),
    ("Plan Change Request", [
        "change plan", "upgrade plan", "downgrade plan", "plan modification",
        "switch plan", "new plan", "better plan",
    ], 0.8),
    ("Service Quality Issue", [
        "service quality", "poor service", "bad service", "service problem",
    ], 0.75),
    ("Service Interruption", [
        "service interruption", "service disruption", "service down", "service unavailable",
    ], 0.8),
    ("Service Configuration", [
        "service configuration", "configure service", "service setup", "service settings",
    ], 0.75),
    ("Service Migration", [
        "service migration", "migrate service", "service transfer", "service move",
    ], 0.75),
    ("Service Bundle Dispute", [
        "service bundle", "bundle issue", "package dispute", "bundle problem",
    ], 0.75),
    ("Service Add-on Request", [
        "add service", "service add-on", "additional service", "extra service",
    ], 0.75),
    ("Service Removal Request", [
        "remove service", "service removal", "cancel service", "discontinue service",
    ], 0.8),
    ("Service Renewal", [
        "service renewal", "renew service", "service extension", "extend service",
    ], 0.75),
    
    # Device & Equipment (76-85)
    ("Incorrect Device / Device Return", [
        "incorrect device", "device has been collected", "returned device",
        "credit cust for the returned device", "device that she already paid for",
        "billed for a device that", "already paid for",
    ], 0.9),
    ("Device Obligation / Insurance Dispute", [
        "device obligation", "device insurance", "device subscription fee",
        "charged for insurance", "cancelled device insurance", "device obligation fee",
        "device obligation charges", "device obligation fee to monthly",
        "once off payment", "once off activation", "monthly installments",
        "device device obligation", "won't be able to pay", "device obligation fee",
        "device abligation", "abligation fee", "early up grade", "new contract",
        "cancelled insurance", "subscriptions of cancelled insurance", "credit of r",
    ], 0.85),
    ("Device Replacement Request", [
        "replace device", "device replacement", "new device", "device exchange",
    ], 0.8),
    ("Device Warranty Issue", [
        "device warranty", "warranty claim", "warranty issue", "warranty problem",
    ], 0.8),
    ("Device Repair Request", [
        "repair device", "device repair", "fix device", "device maintenance",
    ], 0.75),
    ("Device Upgrade Request", [
        "upgrade device", "device upgrade", "new device model", "better device",
    ], 0.75),
    ("Device Return Policy", [
        "return device", "device return policy", "return policy", "device refund",
    ], 0.75),
    ("Device Payment Plan", [
        "device payment", "device installment", "device finance", "device payment plan",
    ], 0.75),
    ("Device Compatibility Issue", [
        "device compatibility", "compatible device", "device support", "device compatibility issue",
    ], 0.7),
    ("Device Activation Issue", [
        "device activation", "activate device", "device setup", "device configuration",
    ], 0.75),
    
    # Fraud & Security (86-90)
    ("Fraud or Identity Dispute", [
        "fraud", "discrepancy", "name cleared", "submitted documents",
        "did not apply for a service", "have her name cleared",
    ], 0.9),
    ("Identity Theft", [
        "identity theft", "stolen identity", "identity fraud", "identity issue",
    ], 0.85),
    ("Unauthorized Access", [
        "unauthorized access", "unauthorized use", "unauthorized charge", "unauthorized transaction",
    ], 0.85),
    ("Security Breach", [
        "security breach", "data breach", "security issue", "security problem",
    ], 0.85),
    ("Account Compromise", [
        "account compromised", "compromised account", "account hacked", "account security breach",
    ], 0.85),
    
    # Customer Service & Complaints (91-95)
    ("Customer Service / Complaint", [
        "complaint", "dissatisfied", "unhappy", "poor service", "bad service",
        "customer service", "not satisfied", "issue with service", "problem with",
        "need help", "assistance required", "support needed",
        "unhappy with", "dissatisfied with", "complaining", "not happy", "frustrated",
    ], 0.7),
    ("Service Complaint", [
        "service complaint", "complain about service", "service issue complaint",
    ], 0.75),
    ("Billing Complaint", [
        "billing complaint", "complain about bill", "invoice complaint",
    ], 0.75),
    ("General Inquiry", [
        "inquiry", "question", "query", "information request", "need information",
        "enquiry", "enquiries", "would like to know", "need to know", "clarification",
        "asking about", "wanted to ask", "request information",
    ], 0.6),
    ("Feedback / Suggestion", [
        "feedback", "suggestion", "comment", "review", "rating",
    ], 0.65),
    
    # Internal Operations (96-100)
    ("Re-logged / Referral", [
        "re-logged to the correct group", "refer to case", "relog to",
        "view case:", "escalated to",
    ], 0.85),
    ("Case Escalation", [
        "escalate case", "case escalation", "escalate issue", "escalate dispute",
    ], 0.8),
    ("Internal Transfer", [
        "transfer case", "case transfer", "move case", "reassign case",
    ], 0.75),
    ("Case Follow-up", [
        "follow up", "case follow-up", "status update", "case update",
    ], 0.7),
    ("Case Closure", [
        "close case", "case closure", "resolve case", "case resolved",
    ], 0.75),
    # New categories from uncategorised analysis
    ("Discount / Settlement Offer (EDC)", [
        "as per discount", "discount offer", "discount from edc", "offer from edc",
        "settlement offer", "settlment offer", "settlement discount", "settlment discount",
        "discount settlement", "edc bham", "edc debt", "edc vvm", "edc hp", "edc saya",
        "edc debt-in", "debt in jaco", "bham jaco", "25% discount", "settlement discount offered",
        "close - settlement discount", "discount received", "settlement received from",
        "nudebt", "nu debt", "discount to be cleared", "balalce of", "balance of r",
        "to be cleared", "settlment offer paid", "edc settlment", "wasp discounts",
        "monthly wasp", "wassp", "wasp discounts for december", "approved by management",
        "bham & dhaya", "bham &", "settlment credt",
    ], 0.88),
    ("Bad Debt / Final Account Clearance", [
        "bad debt", "ad debt", "bad debt to clear", "cleared as bad debt",
        "clear f/acc", "clear f acc", "cr final acc", "final acc less",
        "final acc", "acc less r100", "less r100", "bad debts less than",
        "bad debt r", "to clear", "cleared", "r100 00", "under r100",
    ], 0.88),
    ("Prescribed Debt / Prescription Claim", [
        "prescribed debt", "prescription", "claim prescription", "bureau solutions",
        "bureau solutions claim", "solutions claim prescription", "consumer has claimed prescription",
        "in collection since", "prescription claim",
    ], 0.88),
    ("Payment / FA Allocation (CUST PAID)", [
        "cust paid", "cust paid r", "fa paid", "paid r", "pd 17 jan", "cust pd",
        "transfer funds to f/a", "transfer funds to fa", "transfer funds",
        "proof of pay", "receipt attached", "fa reflecting", "accout up to date",
        "successful naedo", "naedo on", "naedo on 15", "naedo on 30", "naedo on 31",
        "paid on", "payment reflecting",
    ], 0.85),
    ("Penalty / Clawback", [
        "penalty", "clawback", "penalty/clawback", "penalty fee", "penalty clawback",
        "early termination penalty", "termination penalty", "penalty fee not justified",
        "disptuing penalty", "penalty/clawback - fa",
    ], 0.88),
    ("Subscription / FA (Administrative)", [
        "subscription - fa", "subscription fa", "subscription with no usage",
        "subscription", "resolution protection", "resolution protection - fa",
        "poa ongoing", "poa pending", "protection fa", "res protection",
    ], 0.78),
    ("Referral / Cross-Reference", [
        "refer to", "refer to case", "refer -", "refer case", "refer ase",
        "refer 90", "refer 91", "view case", "ref no", "as per ref",
        "as per previous", "as per previous discussions",
    ], 0.75),
    ("Rental", [
        "rental",
    ], 0.8),
    ("Interest Reversal / Credit Interest", [
        "interest reversed", "cr interest", "cr interest r", "credit interest",
    ], 0.82),
    ("Wrong FA / Wrong Account Payment", [
        "wrong fa", "paying into wrong fa", "wrong fa hence", "cst paying into wrong",
    ], 0.85),
    ("Suspension Error / Incorrect Suspension", [
        "incorrectly suspended", "wrongfully suspended",
    ], 0.85),
    ("Reconnection / Soft Cap", [
        "soft cap", "reconnection fee", "reconnection fees", "reconnect fee", "reconnect fees",
        "reconnexion", "reconnections fees", "reconnection", "charged a reconnection fee",
        "reconnections fees also",
    ], 0.8),
    ("Pay Over / Collection Agency", [
        "pay over from", "pay over from nu", "waiting for pay over", "nu debt of",
        "awaiting pay over", "from nudebt",
    ], 0.82),
    ("Mandate / Bank Details Update", [
        "no mandate", "update bank detail", "mandate now", "bank detail not done",
        "call centre said she had no mandate", "update bank details",
    ], 0.82),
    ("Device Return / Modem Issue", [
        "returned the device", "modem was not working", "speed was slow",
        "device as the modem",
    ], 0.85),
    ("Early Termination", [
        "early termination", "early termination penalty",
    ], 0.85),
    # Fallback: broad keywords to reduce uncategorised (low confidence so specific categories win)
    ("General Dispute / Other", [
        "dispute", "disputing", "disputed", "disputes", "disputation",
        "request", "requested", "requesting", "requests",
        "assist", "assistance", "assisted", "please assist", "kindly assist",
        "help", "need help", "require help", "customer need",
        "complaint", "complaints", "complain", "complained",
        "enquiry", "enquiries", "query", "queries", "question", "questions",
        "issue", "issues", "problem", "problems", "matter", "concern",
        "regarding", "with regard", "about the", "regarding the",
        "customer", "client", "subscriber", "account holder",
        "account", "bill", "billing", "invoice", "payment", "charge", "charges",
        "credit", "refund", "debit", "amount", "balance", "outstanding",
        "telkom", "service", "contract", "number", "line", "sim",
        "escalat", "follow up", "followup", "case", "ticket", "reference",
        "please", "kindly", "urgent", "asap", "thank", "thanks",
        "test", "description", "unable to get hold", "get hold of cust", "protected till",
        "resolved", "notes", "send it to", "physical address", "inocrrect", "incorrect",
    ], 0.5),
]


def _normalize_text(text: str) -> str:
    """
    Normalize memo text so keyword matching is more robust.
    Uses pre-compiled regexes for speed.
    """
    if not text:
        return ""
    t = str(text).lower().strip()
    t = _RE_NL.sub(" ", t)
    t = _RE_PUNCT.sub(" ", t)
    t = _RE_SPACES.sub(" ", t).strip()
    return t


def categorize_memo(memo: Optional[str]) -> Tuple[str, float]:
    """
    Assign a category and confidence score to a dispute based on MEMO_TEXT.
    Uses normalized text (so punctuation/newlines don't block matches) and
    multi-keyword scoring (categories with more matching keywords score higher).

    Returns:
        Tuple of (Category Name, Confidence Score)
        If no match: ("Uncategorised", 0.0)
    """
    if not memo or not str(memo).strip():
        return ("Uncategorised", 0.0)

    raw = str(memo).lower().strip()
    # Normalized text: punctuation and newlines as spaces, collapsed spaces
    text = _normalize_text(memo)
    text_with_padding = f" {text} "

    best_match = None
    best_score = 0.0

    for category_name, keywords, base_confidence in CATEGORY_RULES:
        match_count = 0
        max_keyword_confidence = 0.0

        for keyword in keywords:
            kw_lower = keyword.lower().strip()
            if not kw_lower:
                continue
            # Match in normalized text so "rejection-fee" and "rejection fee" both match
            if kw_lower not in text and kw_lower not in raw:
                continue
            # Prefer normalized text for phrase check
            if f" {kw_lower} " in text_with_padding or f" {kw_lower} " in f" {raw} ":
                conf = base_confidence
            else:
                conf = base_confidence * 0.9
            match_count += 1
            if conf > max_keyword_confidence:
                max_keyword_confidence = conf

        if match_count == 0:
            continue
        # Multi-keyword boost: more matching keywords => higher score (max +0.08 for 5+ matches)
        extra = min(match_count - 1, 4) * 0.02
        score = min(max_keyword_confidence + extra, 1.0)
        if score > best_score:
            best_score = score
            best_match = (category_name, round(score, 2))

    if best_match:
        return best_match

    # Last-resort: assign General Dispute / Other if memo contains any common dispute word
    fallback_words = (
        "dispute", "disputing", "request", "assist", "help", "complaint", "query",
        "enquiry", "customer", "account", "bill", "payment", "charge", "credit",
        "refund", "service", "telkom", "amount", "balance", "invoice", "debit",
        "cust", "fa", "discount", "settlement", "clear", "refer", "subscription",
        "interest", "paid", "d/o", "spoke to", "inv", "protection",
    )
    words = set(re.split(r"\s+", text))
    for w in fallback_words:
        if w in words or w in text:
            return ("General Dispute / Other", 0.45)
    return ("Uncategorised", 0.0)


def get_all_categories() -> list:
    """Get list of all categories."""
    return [cat[0] for cat in CATEGORY_RULES] + ["Uncategorised"]
