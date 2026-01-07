# Mortgage Tracker — Starter Lender List (v0.1)

This is a **starter roster** (50 total) for `mortgage-tracker`.  
Links below point to each institution’s primary website (and sometimes a mortgage/rates page when easy to identify).

> Notes:
> - Many lenders don’t publish static rate tables; some require a quote flow.
> - We’ll refine this list into `sources.yaml` (with “scrape method” + “rate page URL”) as we implement parsers.

---

## Massachusetts-focused (25)

### Credit Unions (15)
1. **DCU (Digital Federal Credit Union)** — https://www.dcu.org/  
   - Mortgage rates page: https://www.dcu.org/borrow/mortgage-loans/home-mortgage-loans.html  
2. **Rockland Federal Credit Union** — https://www.rfcu.com/  
3. **Metro Credit Union (MA)** — https://www.metrocu.org/  
   - Mortgage quote page: https://www.metrocu.org/mortgage-rate-quote  
4. **Workers Credit Union** — https://www.wcu.com/  
5. **Jeanne D’Arc Credit Union** — https://www.jdcu.org/  
6. **BrightBridge Credit Union** — https://www.brightbridge.com/  
7. **Hanscom Federal Credit Union** — https://www.hfcu.org/  
8. **Greylock Federal Credit Union** — https://www.greylock.org/  
9. **Webster First Federal Credit Union** — https://www.websterfirst.com/  
10. **St. Anne’s Credit Union** — https://www.stannes.com/  
11. **MIT Federal Credit Union** — https://www.mitfcu.org/  
12. **Quincy Credit Union** — https://www.qcu.org/  
13. **UMassFive College Federal Credit Union** — https://umassfive.coop/  
14. **City of Boston Credit Union** — https://cityofbostoncu.com/  
15. **Align Credit Union** — https://www.aligncu.com/  

### Banks (10)
16. **Eastern Bank** — https://www.easternbank.com/  
17. **Rockland Trust** — https://www.rocklandtrust.com/  
18. **Cambridge Savings Bank** — https://www.cambridgesavings.com/  
19. **Middlesex Savings Bank** — https://www.middlesexbank.com/  
20. **Salem Five Bank** — https://www.salemfive.com/  
21. **Needham Bank** — https://www.needhambank.com/  
22. **Cape Cod 5** — https://www.capecodfive.com/  
23. **Berkshire Bank** — https://www.berkshirebank.com/  
24. **Brookline Bank** — https://www.brooklinebank.com/  
25. **HarborOne Bank** — https://www.harborone.com/  

---

## Nationwide (25)

### Large / established credit unions (10)
1. **Navy Federal Credit Union** — https://www.navyfederal.org/  
2. **State Employees’ Credit Union (NCSECU)** — https://www.ncsecu.org/  
3. **PenFed Credit Union** — https://www.penfed.org/  
4. **SchoolsFirst FCU** — https://www.schoolsfirstfcu.org/  
5. **BECU** — https://www.becu.org/  
6. **Golden 1 Credit Union** — https://www.golden1.com/  
7. **Alliant Credit Union** — https://www.alliantcreditunion.org/  
8. **America First Credit Union (UT)** — https://www.americafirst.com/  
9. **First Tech Federal Credit Union** — https://www.firsttechfed.com/  
10. **Patelco Credit Union** — https://www.patelco.org/  

### Large / common national lenders (15)
11. **United Wholesale Mortgage (UWM)** — https://www.uwm.com/  *(wholesale / broker channel)*  
12. **Rocket Mortgage** — https://www.rocketmortgage.com/  
13. **Pennymac** — https://www.pennymac.com/  
14. **Newrez** — https://www.newrez.com/  
15. **Mr. Cooper** — https://www.mrcooper.com/  
16. **loanDepot** — https://www.loandepot.com/  
17. **Rate (Guaranteed Rate)** — https://www.rate.com/  
18. **CrossCountry Mortgage** — https://crosscountrymortgage.com/  
19. **Guild Mortgage** — https://www.guildmortgage.com/  
20. **Fairway Independent Mortgage** — https://www.fairway.com/  
21. **Movement Mortgage** — https://movement.com/  
22. **Freedom Mortgage** — https://www.freedommortgage.com/  
23. **AmeriHome Mortgage** — https://www.amerihome.com/  
24. **Chase (JPMorgan Chase)** — https://www.chase.com/personal/mortgage  
25. **Wells Fargo** — https://www.wellsfargo.com/mortgage/  

---

## Next edits we’ll make
- Add “rate_url” per source (direct rate table / disclosures / quote endpoint).
- Add tags: `MA_local`, `national`, `cu`, `bank`, `nonbank`, `needs_quote_flow`.
- Mark `is_favorite` / `is_excluded` as you curate over time.
