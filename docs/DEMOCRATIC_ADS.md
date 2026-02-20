# 🗳️ Democratic Ad Sorting

**How the community decides what gets shown.**

---

## 🎯 The Problem with Traditional Ads

Traditional advertising:
```
Highest bidder wins → Spam rises → Users ignore → Everyone loses
```

Our system:
```
Community votes → Useful stuff rises → Users engage → Businesses succeed
```

---

## 📊 How Sorting Works

### The Algorithm (Simplified)

```
Score = (Upvotes - Downvotes) × CTR Multiplier × Recency Factor

Where:
• Upvotes: Users who found this useful
• Downvotes: Users who found this spammy
• CTR Multiplier: How often people click (1.0 = average, 2.0 = great)
• Recency Factor: Fresh content gets slight boost
```

### Example Calculation

```
Business A:
• Upvotes: 200
• Downvotes: 20
• CTR: 15% (multiplier: 1.5)
• Recency: 0.95 (listed 2 weeks ago)

Score = (200 - 20) × 1.5 × 0.95 = 256.5

Business B:
• Upvotes: 50
• Downvotes: 5
• CTR: 8% (multiplier: 0.8)
• Recency: 1.0 (listed yesterday)

Score = (50 - 5) × 0.8 × 1.0 = 36

Result: Business A ranks higher (earned it)
```

---

## 🗳️ Voting System

### How to Vote

**Upvote (👍) if:**
- Service is legitimate
- Description is clear
- You'd recommend to a friend
- Portfolio looks professional

**Downvote (👎) if:**
- Looks like spam
- Misleading description
- Broken links
- Poor quality work
- Rude to customers

**Flag (⚠️) if:**
- Scam/fraud
- Stolen content
- Adult/NSFW
- Non-modding service
- Rules violation

### Vote Weighting

Not all votes are equal:

```
New account (0-10 votes cast): 0.5x weight
Established user (10-100 votes): 1.0x weight
Trusted user (100+ votes, good track record): 1.2x weight
```

**Why?** Prevents vote manipulation, rewards engaged community members.

---

## 📈 Ranking Factors

### Primary Factors (80% of score)

| Factor | Weight | What It Means |
|--------|--------|---------------|
| Vote Ratio | 40% | Upvotes vs downvotes |
| Total Votes | 20% | More votes = more data |
| CTR | 20% | Do people actually click? |

### Secondary Factors (20% of score)

| Factor | Weight | What It Means |
|--------|--------|---------------|
| Recency | 10% | Fresh content gets boost |
| Reviews | 5% | User feedback after using |
| Response Rate | 5% | Business engages with users |

---

## 🎯 Tier System

### How Tiers Work

```
Tier 1 (Starter): 0-100 votes
• FREE clicks
• Learning phase
• Basic visibility

Tier 2 (Growing): 100-500 votes
• $5 per 1000 clicks
• Established credibility
• Good visibility

Tier 3 (Community Favorite): 500+ votes
• $2.50 per 1000 clicks (50% discount!)
• Proven track record
• Premium visibility
```

### Tier Benefits

**Tier 1 → Tier 2:**
- Unlock analytics dashboard
- Priority support
- Custom branding options

**Tier 2 → Tier 3:**
- 50% cost reduction
- Featured rotation (sometimes)
- Badge on listing

---

## 🛡️ Anti-Manipulation

### What We Detect

**Vote Stuffing:**
```
❌ Business owner upvoting themselves
❌ Asking friends to mass upvote
❌ Bot votes
❌ Vote trading ("I'll upvote if you...")
```

**Detection Methods:**
- IP address analysis
- Voting pattern recognition
- Account age/behavior
- Click fraud detection

**Penalties:**
```
First time: Reset votes, warning
Second time: 30-day suspension
Third time: Permanent ban
```

### Click Fraud

**We filter out:**
- Self-clicks (business owner)
- Bot traffic
- Accidental clicks (bounce <2 seconds)
- Click farms

**You only pay for:**
- Real modders
- Intentional clicks
- Engaged visitors

---

## 📊 Transparency

### Public Metrics

Anyone can see:
- Total active listings
- Average vote scores by category
- Top-rated businesses (no revenue info)

### Business Dashboard

Listings can see:
- Their vote breakdown
- Daily/weekly trends
- Click analytics
- Competitor benchmarks (aggregated)

### User Dashboard

Users can see:
- Their voting history
- Impact of their votes
- Flagged content status

---

## 🎯 Strategy for Businesses

### Earn Votes Organically

**DO:**
✅ Deliver quality work
✅ Respond quickly to inquiries
✅ Update listing regularly
✅ Add portfolio pieces
✅ Engage with community
✅ Offer free resources/tips

**DON'T:**
❌ Ask for upvotes directly
❌ Offer incentives for votes (bribes)
❌ Vote manipulate
❌ Spam other listings
❌ Fake portfolio

### Long-Term Success

```
Month 1: Focus on quality work → Get natural votes
Month 2: Reach Tier 2 → Optimize listing
Month 3: Maintain quality → Reach Tier 3
Month 4+: Enjoy 50% discount + premium placement
```

**Short-term thinking:** Game the system → Get caught → Banned

**Long-term thinking:** Build reputation → Earn votes → Sustainable growth

---

## 🤝 For Users: Why Vote?

### Your Vote Matters

```
You upvote a good business → It rises → More modders find it → Community wins

You downvote spam → It sinks → Less spam → Better experience for everyone
```

### Voting is Anonymous

- Businesses can't see who voted
- No retaliation possible
- Your vote is secret

### Voting Helps You

- Better listings rise
- Less spam shown
- Community improves
- Your experience gets better

---

## 📈 Example: Good vs Bad Listing

### Good Listing Trajectory

```
Week 1:
• Listing created: "Custom Armor Ports"
• Portfolio: 5 examples
• Initial votes: 12 (from past clients)
• Score: 15.2

Week 4:
• Votes: 89
• CTR: 14% (people interested)
• Score: 112.5
• Rank: #5 in category

Week 12:
• Votes: 520 (Tier 3!)
• CTR: 18% (excellent)
• Score: 890.3
• Rank: #2 in category
• Cost: 50% discount

Result: Sustainable business, happy customers
```

### Bad Listing Trajectory

```
Week 1:
• Listing created: "BEST MODZ BUY NOW!!!"
• Portfolio: None
• Initial votes: 3 (all downvotes)
• Score: -2.1

Week 2:
• Votes: 23 (90% negative)
• CTR: 2% (nobody clicking)
• Score: -15.4
• Rank: #47 in category

Week 3:
• Flagged by users
• Manual review
• Removed for spam

Result: Wasted time, banned
```

---

## ❓ FAQ

### Q: Can businesses see who downvoted them?

**A:** No. Votes are completely anonymous.

### Q: What if a competitor downvotes me?

**A:** We detect patterns. Mass downvotes from suspicious accounts are invalidated.

### Q: Can I change my vote?

**A:** Yes, within 7 days. After that, it's locked.

### Q: Do votes expire?

**A:** No, but older votes have slightly less weight than recent ones.

### Q: What if I accidentally voted wrong?

**A:** You can change it within 7 days in your dashboard.

### Q: Can businesses pay for better placement?

**A:** No. Only community votes determine ranking. Money only affects billing tier.

---

## 🎯 Principles

1. **Community knows best** — Users decide what's valuable
2. **Transparency** — Algorithm is open-source
3. **Anti-manipulation** — Cheating is detected and punished
4. **Long-term thinking** — Rewards quality, not spam
5. **Democratic** — One user, one vote (weighted by engagement)

---

## 📞 Report Manipulation

See something suspicious?

**Flag it:**
- Click ⚠️ on the listing
- Describe what you saw
- We investigate within 24 hours

**Or email:**
- abuse@skymodderai.example
- Include evidence
- Anonymous reports accepted

---

**Last updated:** February 20, 2026

*Powered by the community, for the community.* 🗳️
