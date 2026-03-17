# Full Advertising & Growth Strategy
## Autonomous App Studio — Park-It & Surve
### Prepared by: Marketing Lead | March 17, 2026

---

# PART 1: PARK-IT — Full Marketing Strategy

## 1. App Store Optimization (ASO)

### App Store Listing

**Title (30 chars max):**
`Park-It: Find My Parked Car`

**Subtitle (30 chars max):**
`Save Spot & Navigate Back Fast`

**Keyword Field (100 chars, comma-separated):**
`parking,find my car,parked car,parking spot,where did I park,car finder,parking tracker,GPS park,lot`

**Category:** Primary: `Navigation` | Secondary: `Utilities`

### App Store Description

```
Never lose your car again.

Park-It is the simplest way to save your parking spot and navigate back to your car. One tap saves your exact GPS location — then find your way back with turn-by-turn directions when you're ready.

INSTANT PARKING SAVE
Tap the Park-It button and your car's exact GPS location is saved instantly. No typing, no photos, no hassle. Just one tap.

FIND YOUR CAR, FAST
See exactly how far away your car is, with real-time distance tracking. Tap "Find My Car" to get turn-by-turn navigation straight to your spot via Apple Maps.

LIVE PARKING TIMER
Track how long you've been parked with a real-time elapsed timer. Never overstay a meter or time-limited spot again.

FULL PARKING HISTORY
Every parking session is saved — see where you parked, when, and for how long. Swipe to delete sessions you no longer need.

MANAGE YOUR VEHICLES
Add multiple vehicles with make, model, color, and license plate. Keep everything organized across your household.

PREMIUM DESIGN
Monochrome, Uber-inspired interface. No clutter. No ads. Just a beautiful, functional parking companion.

DARK MODE
Full dark mode support for comfortable use at any hour.

PRIVACY FIRST
Your parking data stays on your device and in your secure account. We never sell your location data.

Download Park-It today and never circle the block again.
```

### Screenshot Brief (5 Screens — iPhone 6.7")

| # | Screen | Headline | Subtext |
|---|--------|----------|---------|
| 1 | Park button (idle state, dark BG) | **One Tap. Parked.** | Save your exact spot instantly |
| 2 | Active parking with timer + distance | **Always Know Where You Parked** | Live timer & distance tracking |
| 3 | Find My Car navigation | **Navigate Back in Seconds** | Turn-by-turn to your car |
| 4 | History tab with sessions | **Your Complete Parking History** | Every session, every detail |
| 5 | Profile with vehicles | **Manage All Your Vehicles** | Track cars for the whole family |

**Design notes:** Black (#111827) backgrounds, white (#F9FAFB) text, green (#059669) accents on active states. No device bezels — full-bleed screenshots with text overlays above the app UI. Use SF Pro Display Bold for headlines.

### A/B Test Plan
- **Test A:** "One Tap. Parked." vs "Never Lose Your Car Again" as screenshot 1 headline
- **Test B:** Lead with the Find My Car screen vs the Park button screen
- **Test C:** Add a "FREE" badge vs no badge on screenshot 1

### Rating/Review Strategy
- Prompt for review after 3rd successful "car retrieved" action (high-satisfaction moment)
- Use `SKStoreReviewController` — max 3 prompts per 365-day period
- Never prompt during first session or during active parking

---

## 2. Paid User Acquisition Plan

### Apple Search Ads — Campaign Structure

**Budget:** $2,000/month initial (scale to $5,000 at positive ROAS)

| Campaign | Match Type | Keywords | Bid Range | Daily Budget |
|----------|-----------|----------|-----------|-------------|
| **Brand** | Exact | park-it, park it app, parkit | $0.50-1.00 | $10 |
| **Category** | Broad | parking app, find my car, parking finder, car locator, parking spot finder | $1.50-3.00 | $25 |
| **Competitor** | Exact | spothero, parkwhiz, bestparking, parkme, honk parking | $2.00-4.00 | $15 |
| **Discovery** | Search Match | (auto) | $1.00-2.50 | $15 |

**Expected CAC:** $1.50-3.50 per install (Navigation category avg: $2.80)

### Meta Ads (Facebook + Instagram)

**Budget:** $1,500/month

**Audience Targeting:**

| Audience | Targeting | Budget Split |
|----------|-----------|-------------|
| **Core** | Interest: Driving, Urban living, Commuting, Parking; Age 22-45; Metro areas (NYC, LA, SF, Chicago, Boston, Seattle, Miami, DC) | 40% |
| **Lookalike** | 1% LAL based on app installers (after 500+ installs) | 30% |
| **Retargeting** | Website visitors, app page visitors who didn't install | 15% |
| **Broad** | Age 25-55, major metro areas, iOS only | 15% |

**Ad Creative Variants (A/B Testing):**

**Variant 1 — Problem/Solution (Static Image)**
> Headline: "Stop Circling the Block"
> Primary text: "One tap saves your parking spot. Find your car with GPS navigation. It's that simple."
> CTA: Install Now

**Variant 2 — Social Proof (Static Image)**
> Headline: "The Parking App Urban Drivers Love"
> Primary text: "Save your spot in one tap. Navigate back in seconds. Join thousands of drivers who never lose their car."
> CTA: Install Now

**Variant 3 — UGC-Style (Video 15s)**
> Hook (0-3s): Person looking confused in parking garage, text overlay "WHERE DID I PARK??"
> Middle (3-10s): Opens Park-It, taps Find My Car, walks confidently
> End (10-15s): Arrives at car, text "Park-It — never lose your car again"

**Variant 4 — Feature Demo (Video 6s)**
> Quick screen recording: Tap Park-It button → timer starts → tap Find My Car → navigation opens
> Text overlay: "One tap. Done."

**Variant 5 — Pain Point (Carousel)**
> Slide 1: "Remember where you parked? Neither do we."
> Slide 2: Park-It button screenshot
> Slide 3: Find My Car navigation screenshot
> Slide 4: "Download Park-It — Free" with CTA

**Expected CAC:** $2.00-4.50 per install

### TikTok Ads

**Budget:** $500/month (test phase)

**Ad Concepts:**

1. **"POV: You forgot where you parked"** — Relatable humor, show the frustration then the solution. UGC-style with trending audio.
2. **"Things I can't live without in [city]"** — Listicle format, Park-It featured among urban essentials.
3. **"This app saved me 20 minutes today"** — Testimonial-style with screen recording overlay.

**Targeting:** Age 18-35, interests: cars, driving, city life, tech apps. Top 10 US metros.

**Expected CAC:** $1.50-3.00 (TikTok installs trend cheaper for utility apps)

### Total Paid Budget Summary

| Channel | Monthly Budget | Expected Installs | Expected CAC |
|---------|---------------|-------------------|-------------|
| Apple Search Ads | $2,000 | 570-1,330 | $1.50-3.50 |
| Meta Ads | $1,500 | 330-750 | $2.00-4.50 |
| TikTok Ads | $500 | 165-330 | $1.50-3.00 |
| **Total** | **$4,000** | **1,065-2,410** | **$1.66-3.76 avg** |

### Attribution Setup
- **SKAdNetwork (SKAN 4.0):** Configure conversion value mapping — map install → signup → first park → 3rd park as conversion milestones
- **Meta:** Install Meta SDK, configure app events for `CompleteRegistration`, `CustomEvent_ParkCar`, `CustomEvent_FindCar`
- **TikTok:** Install TikTok Events SDK, mirror same events

---

## 3. Organic Growth Strategy

### Social Media Content Calendar — 4 Weeks (Instagram + TikTok)

#### Week 1: Problem Awareness

| Day | Platform | Format | Content | Caption |
|-----|----------|--------|---------|---------|
| Mon | IG | Reel (15s) | POV: Walking around a parking garage confused | "We've all been here. Park-It fixes this. Link in bio. #parking #citylife #lifehack" |
| Tue | TikTok | Video (10s) | Screen recording of one-tap park flow | "One tap. That's it. #parkit #parkingapp #cartok" |
| Wed | IG | Carousel | "5 Signs You Need a Parking App" infographic | "If you've ever circled the block for 15 minutes... you need this. #urbandriving" |
| Thu | TikTok | Stitch | React to "worst parking experiences" videos | "Never again. #parkit #relatable" |
| Fri | IG | Story Poll | "Have you ever forgotten where you parked?" Yes/No | Drive engagement, lead into app teaser |

#### Week 2: Product Showcase

| Day | Platform | Format | Content | Caption |
|-----|----------|--------|---------|---------|
| Mon | IG | Reel (20s) | Full app demo — park, timer, find car | "Park-It in 20 seconds. The only parking app you need. #appofthedayday" |
| Tue | TikTok | Video (15s) | "Things on my phone I actually use" format | "This one actually saves me time every single day #parkit" |
| Wed | IG | Static Post | Dark screenshot of the Park button, clean design | "Designed to be beautiful. Built to be useful. Park-It." |
| Thu | TikTok | Duet | Duet with parking fail videos, show Park-It solution | "Should've had Park-It #parkingfail" |
| Fri | IG | Story | Behind-the-scenes: design process, monochrome palette | "Why we made Park-It black & white (thread)" |

#### Week 3: Social Proof & Community

| Day | Platform | Format | Content | Caption |
|-----|----------|--------|---------|---------|
| Mon | IG | Reel | User testimonial compilation (or simulated early reviews) | "Here's what drivers are saying about Park-It" |
| Tue | TikTok | Video | "Day in my life in NYC" — featuring Park-It moment | "My secret weapon for city parking #nyclife #parkit" |
| Wed | IG | Carousel | "Park-It vs. Wandering Around Lost" comparison | "The data doesn't lie. Save 15 min every time you park." |
| Thu | TikTok | Video | Quick tip: "Did you know you can track how long you've been parked?" | "No more parking tickets #parkit #lifehack" |
| Fri | IG | Story Q&A | "What's your worst parking story?" | Engagement builder, share responses Mon |

#### Week 4: Conversion Push

| Day | Platform | Format | Content | Caption |
|-----|----------|--------|---------|---------|
| Mon | IG | Reel | Compilation of Week 3 Q&A parking horror stories | "You asked, we listened. These stories are wild. Download Park-It so this never happens to you." |
| Tue | TikTok | Video | "Rating parking apps" — review format, Park-It wins | "10/10 no notes #parkit #appreview" |
| Wed | IG | Static | Clean screenshot with "Free on the App Store" badge | "Available now. Link in bio." |
| Thu | TikTok | Video | Speed comparison: finding car with vs without Park-It | "15 minutes vs 15 seconds #parkit" |
| Fri | IG + TT | Reel/Video | Launch week recap, CTA to download | "Week 1 in the books. Thank you. This is just the beginning." |

### SEO Content Topics (Blog/Web Presence)

1. "How to Never Lose Your Car in a Parking Garage Again"
2. "The Best Parking Apps for City Drivers in 2026"
3. "Parking in [City]: A Complete Guide" (create for top 10 metros)
4. "How GPS Parking Apps Save You Time and Money"
5. "Street Parking vs Garage Parking: Pros, Cons, and Tips"
6. "Why Every Urban Driver Needs a Parking Tracker App"

**Target keywords:** find my car app, parking spot saver, where did I park, parking tracker, GPS car finder, parking app free

### Community Building

**Reddit:**
- Monitor and engage in: r/parking, r/urbanplanning, r/cars, r/[cityname] subreddits
- Share genuine value (parking tips) before mentioning app
- Post in r/apple and r/iphone during launch week (follow self-promo rules)
- Create an r/ParkItApp subreddit for feature requests and feedback

**Local Partnerships:**
- Reach out to city parking blogs and local lifestyle influencers
- Partner with parking garage operators for cross-promotion

---

## 4. Launch Checklist

### Pre-Launch (Weeks -4 to -1)

| Week | Tasks |
|------|-------|
| **Week -4** | Finalize ASO (title, subtitle, keywords, description). Submit app for App Store review. Set up social media accounts (IG, TikTok, X). Create landing page with email capture. |
| **Week -3** | Begin posting teaser content on social (3x/week). Set up Apple Search Ads account. Configure Meta Business Suite + ad account. Build email list via landing page + friends/family. Start Reddit presence (genuine participation, no promotion yet). |
| **Week -2** | App approved and ready for release. Set release date for Week 0 Monday. Send beta invites to 50-100 testers via TestFlight. Prepare press release. Prepare Product Hunt listing (draft, not submit). Create influencer outreach list (20 micro-influencers in urban/car/tech niches). |
| **Week -1** | Send press release to 30 tech/app bloggers. Reach out to 10 micro-influencers with free access. Schedule launch day social posts. Prepare Apple Search Ads campaigns (paused, ready to activate). Final QA on all marketing assets. Email list: "Launching in 7 days" teaser. |

### Launch Week (Week 0)

| Day | Tasks |
|-----|-------|
| **Monday** | Release app on App Store. Activate all Apple Search Ads campaigns. Post launch announcement on all social channels. Send "We're Live!" email to list. Submit to Product Hunt. |
| **Tuesday** | Activate Meta Ads (start with Variant 1 + Variant 3). Engage with all Product Hunt comments. Share launch on personal networks. Post in relevant subreddits (follow rules). |
| **Wednesday** | Activate TikTok Ads. Post user reaction/download milestone content. Respond to all App Store reviews. Check ad performance, pause underperformers. |
| **Thursday** | Share early metrics/milestones on social. Follow up with press contacts who haven't responded. Adjust ad bids based on 72hr data. |
| **Friday** | Post "Week 1 Recap" content. Analyze first week data: installs, signups, first parks, retention. Plan Week 2 content based on what performed. |

### Post-Launch (Weeks 1-4)

| Week | Tasks |
|------|-------|
| **Week 1** | Analyze D1 retention. Optimize ad creatives (pause bottom 50%, scale top performers). Second round of influencer outreach. Begin A/B testing App Store screenshots. |
| **Week 2** | Analyze D7 retention. Launch retargeting campaigns on Meta. Publish first SEO blog post. Implement review solicitation prompt (after 3rd car retrieval). |
| **Week 3** | Scale winning ad campaigns by 20-30%. Launch referral program (see below). Create lookalike audiences from first 500+ installers. |
| **Week 4** | Full month review: CAC, LTV projections, retention curves. Adjust budget allocation based on channel ROAS. Plan Month 2 content calendar. Prepare first monthly marketing report. |

---

## 5. Referral Program

### Viral Loop Mechanics

**Trigger:** User retrieves their car (high-satisfaction moment) → prompt: "Share Park-It with a friend and you both get Premium for 7 days!"

**Mechanics:**
1. User taps "Share" → generates unique referral link
2. Friend downloads via link → both users unlock Premium features for 7 days
3. If friend refers another user → original referrer gets additional 7 days

**Premium Features (Referral Unlock):**
- Parking duration alerts (push notification at custom time)
- Favorite locations (save frequent parking areas)
- Parking cost tracker (log meter costs)
- Extended history (beyond 30 days)

**Sharing Channels:**
- iMessage (deep link)
- WhatsApp
- Copy link
- Social media share cards (auto-generated image with "I parked [X] times this month with Park-It")

**AARRR Mapping:** This is a **Referral** mechanism that also drives **Acquisition** (new installs) and **Retention** (Premium trial creates habit).

**Expected viral coefficient:** 0.15-0.30 (each user brings 0.15-0.30 new users). Target: 0.3+ after optimization.

---

## 6. KPI Dashboard

### Metrics to Track

| Metric | Definition | Target (Month 1) | Target (Month 3) |
|--------|-----------|-------------------|-------------------|
| **Installs** | Total App Store downloads | 2,000-4,000 | 8,000-15,000 |
| **CAC** | Total spend / installs | $1.50-3.50 | $1.00-2.50 |
| **Signup Rate** | Signups / installs | 60%+ | 70%+ |
| **Activation Rate** | First park / signups | 40%+ | 55%+ |
| **D1 Retention** | Users returning Day 1 | 30%+ | 40%+ |
| **D7 Retention** | Users returning Day 7 | 15%+ | 25%+ |
| **D30 Retention** | Users returning Day 30 | 8%+ | 15%+ |
| **Parks/User/Week** | Avg parking saves per active user per week | 2+ | 3+ |
| **Find My Car Usage** | % of parks that use Find My Car | 50%+ | 60%+ |
| **Referral Rate** | % of users who share referral link | 5%+ | 10%+ |
| **Viral Coefficient** | New users per existing user via referrals | 0.10+ | 0.25+ |
| **App Store Rating** | Average star rating | 4.5+ | 4.7+ |
| **ROAS** | Revenue / ad spend (once monetized) | N/A (free) | Track for Premium |
| **LTV** | Projected lifetime value per user | Establish baseline | $2-5 (freemium) |

### Funnel Benchmarks

```
App Store View → Install:     40-50% (good ASO)
Install → Signup:             60-70%
Signup → First Park:          40-55%
First Park → Find My Car:    50-60%
First Park → 2nd Park:       35-45%
2nd Park → Weekly Active:    25-35%
```

---
---

# PART 2: SURVE — Marketing Strategy

## 1. App Store Optimization (ASO)

### App Store Listing

**Title (30 chars max):**
`Surve: Live Sports Scores`

**Subtitle (30 chars max):**
`Track Any Game in Real-Time`

**Keyword Field (100 chars):**
`sports,scores,live score,scoreboard,score tracker,game score,basketball,football,tennis,cricket,rugby`

**Category:** Primary: `Sports` | Secondary: `Utilities`

### App Store Description

```
Track live sports scores for any game, any sport. Tap to score.

Surve is the simplest way to keep score. Whether you're coaching a team, playing a pickup game, or tracking a tournament — Surve keeps score so you can focus on the game.

TAP TO SCORE
One tap to add a point. Track scores for home and away teams with large, easy-to-tap buttons. Haptic feedback on every score.

10 SPORTS SUPPORTED
Rugby, Football, Basketball, Tennis, Cricket, Baseball, Hockey, Volleyball, Soccer, and Badminton — each with sport-specific scoring and terminology.

REAL-TIME SYNC
Scores sync live to the cloud. Share a game and others can follow along in real-time.

GAME HISTORY
Every game is saved — see final scores, timestamps, and which sport. Browse your complete match history.

BEAUTIFUL DESIGN
Sport-specific color themes and field backgrounds. Clean, distraction-free scoring interface. Dark mode included.

PAUSE & RESUME
Pause games at halftime, resume when ready. Never lose track of the score.

Start scoring smarter. Download Surve today.
```

### Screenshot Brief (5 Screens)

| # | Screen | Headline | Subtext |
|---|--------|----------|---------|
| 1 | Sport selection grid (10 sports) | **Track Any Sport** | Choose your game and start scoring |
| 2 | Live scoring interface (basketball) | **Tap to Score** | Large buttons, haptic feedback |
| 3 | Active game with score and timer | **Real-Time Scoreboard** | Live sync across devices |
| 4 | Game history with completed matches | **Your Match History** | Every game, every score |
| 5 | Profile with stats | **Your Sports Dashboard** | Track your games and streaks |

---

## 2. Growth Strategy — Product-Led Growth (PLG)

Surve's primary growth engine is **the product itself**. Every shared game score is an acquisition channel.

### Viral Loop

```
User tracks a game → Shares score/result → Viewer sees Surve branding →
Viewer downloads Surve → Tracks their own games → Shares → Repeat
```

**Key PLG Tactics:**

1. **Branded score cards:** Every shared game result shows "Scored with Surve" with download CTA
2. **Live score sharing:** Share a live game link — spectators see real-time scores and can download Surve
3. **Share results:** Users can share final scores as images/cards on social media (branded)
4. **Sport communities:** Engage rec league organizers, coaches, and pickup game groups who need easy scoring

**Expected viral coefficient:** 0.3-0.5 (each scorer brings 0.3-0.5 new users via game sharing)

### Paid UA (Phase 2 — After PLG Validation)

Start with organic/PLG for first 2 months. If viral coefficient < 0.3, add:
- Apple Search Ads: $500/month targeting "score tracker", "scoreboard app", "live score"
- Meta Ads: $500/month targeting coaches, rec league players, sports fans
- **Expected CAC:** $2.00-5.00

---

## 3. Content Plan

### Blog/SEO Topics (8 Articles)

1. "How to Track Sports Scores on Your iPhone (Step-by-Step)"
2. "The Best Free Scoreboard Apps for iPhone in 2026"
3. "10 Sports You Can Score with Surve"
4. "Rec League Score Tracking: Why Your League Needs a Digital Scoreboard"
5. "How to Keep Score in Cricket, Rugby & More — The Easy Way"
6. "Surve vs Paper Scoreboards: Why Coaches Are Switching"
7. "How to Share Live Game Scores with Your Team"
8. "Pickup Game Score Tracking: Never Argue About the Score Again"

**Target keywords:** score tracker app, scoreboard app, live score app, sports scoring app, keep score app, game score tracker

### Social Media Calendar — 2 Weeks (Instagram + TikTok)

#### Week 1: Awareness

| Day | Platform | Content |
|-----|----------|---------|
| Mon | IG Reel | "Track any game score in seconds" — speed demo |
| Tue | TikTok | "POV: Nobody remembers the score at halftime" — show Surve as solution |
| Wed | IG Carousel | "10 Sports You Can Score with Surve" — sport showcase |
| Thu | TikTok | "Rating apps for pickup games" — Surve gets 10/10 |
| Fri | IG Story | Poll: "How do you usually keep score?" — engagement driver |

#### Week 2: Conversion

| Day | Platform | Content |
|-----|----------|---------|
| Mon | IG Reel | User testimonial: "Surve is how our rec league tracks every game" |
| Tue | TikTok | "Things I bring to every pickup game" listicle featuring Surve |
| Wed | IG Static | Clean screenshot with "Free on the App Store" |
| Thu | TikTok | Quick demo of basketball scoring — tap to score live |
| Fri | IG + TT | "Thank you for [X] downloads" milestone post |

---

## 4. Launch Plan — Product Hunt Strategy

### Timeline

| When | Action |
|------|--------|
| **Week -2** | Create Product Hunt maker profile. Draft listing: tagline, description, images, first comment. Recruit 5-10 hunter candidates (active PH users with followers). Notify personal network to save the date. |
| **Week -1** | Finalize all PH assets. Schedule launch for Tuesday 12:01 AM PT (best day for engagement). Prepare "first comment" explaining the story behind Surve. Line up 30+ supporters to upvote and comment in first 4 hours. Draft outreach emails to tech bloggers. |
| **Launch Day** | Post at 12:01 AM PT. Share on all social channels. Send email blast. Engage with EVERY comment on PH within 1 hour. Post in relevant Slack/Discord communities. Share on X/Twitter with #producthunt tag. |
| **Day After** | Thank supporters. Share PH results on social. Follow up with all bloggers/press. If Top 5, use badge in all marketing materials. |

**Product Hunt Tagline:** "Track live sports scores for any game. Tap to score."

**First Comment (Maker Comment):**
> Hey Product Hunt! I'm excited to share Surve — the sports score tracker I wish existed.
>
> I built Surve because every time I played a pickup game or coached a match, nobody could remember the score. Surve lets you tap to score for any sport — basketball, football, tennis, cricket, rugby, and more.
>
> What makes Surve different:
> - 10 sports with sport-specific scoring and terminology
> - One-tap scoring with haptic feedback
> - Real-time score sync across devices
> - Full game history with timestamps
> - Dark mode, sport-themed color schemes, native iOS feel
>
> I'd love your feedback — what sports should we add next?

### App Review Site Submissions
- AppAdvice
- AppStoreApps.com
- 148Apps
- AppShopper
- MacStories (if unique angle available)

---
---

# PART 3: FRAMEWORK APPLICATION SUMMARY

## AARRR Mapping

| Stage | Park-It | Surve |
|-------|---------|-------|
| **Acquisition** | ASA, Meta Ads, TikTok, SEO, social content | PLG (shared game scores), PH launch, SEO, social |
| **Activation** | First successful "Park It" tap + car save | First game scored + first game completed |
| **Retention** | Push notifications near saved spots, parking timer alerts, history | Game history, streak badges, sport-specific features |
| **Revenue** | Premium features (alerts, favorites, extended history) | Premium (advanced stats, tournament mode, team management) |
| **Referral** | Share parking spot → both get Premium trial | Every shared game score = acquisition channel + live score CTA |

## Hook Model Implementation

| Element | Park-It | Surve |
|---------|---------|-------|
| **Trigger** | External: Parked car, need to find it. Internal: Anxiety about forgetting location | External: Game starting, need to keep score. Internal: Competitive drive to track results |
| **Action** | Tap Park-It button (minimal effort) | Select sport, tap to score (minimal friction) |
| **Variable Reward** | See exactly how far your car is, discover new parking patterns in history | Watch the score change live, review close games in history |
| **Investment** | Save favorite spots, add vehicles, build parking history | Build game history, track win streaks, develop sport preferences |

## Blue Ocean Positioning

| | Park-It | Surve |
|--|---------|-------|
| **Red Ocean (avoid)** | Competing with Google Maps on navigation, SpotHero on booking | Competing with ESPN/major score apps on professional leagues |
| **Blue Ocean (own)** | "Where's my car?" memory + GPS + instant save. No other app does this one job this well | Mobile-first, tap-to-score for pickup games and rec leagues. No other app makes casual scoring this easy. |
| **Key differentiator** | Monochrome premium design, one-tap UX, parking-only focus | 10 sports, one-tap scoring, sport-specific themes, real-time sync |

---

# PART 4: BUDGET SUMMARY

## Monthly Budget Allocation (Month 1)

| Line Item | Park-It | Surve | Total |
|-----------|---------|-------|-------|
| Apple Search Ads | $2,000 | $0 (PLG first) | $2,000 |
| Meta Ads | $1,500 | $0 | $1,500 |
| TikTok Ads | $500 | $0 | $500 |
| Content Creation (freelance) | $300 | $200 | $500 |
| Influencer Gifting | $200 | $0 | $200 |
| **Total** | **$4,500** | **$200** | **$4,700** |

## Expected Returns (Month 1)

| Metric | Park-It | Surve |
|--------|---------|-------|
| Paid Installs | 1,065-2,410 | 0 (organic only) |
| Organic Installs | 200-500 | 300-800 (PLG + PH) |
| Total Installs | 1,265-2,910 | 300-800 |
| Blended CAC | $1.55-3.56 | $0.25-0.67 (content cost only) |
| Signups | 760-2,040 | 210-560 |
| Activated Users (first game scored) | 300-1,120 | 105-280 |

---

*Strategy prepared by Marketing Lead, Autonomous App Studio. All copy is production-ready. All targeting is specific and actionable. Review quarterly and adjust based on actual performance data.*
