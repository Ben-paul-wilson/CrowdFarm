# Scrum / Daily Log

## Today's Updates

**Authentication & Navigation**
- **Removed Agent Registration**: Removed the option for users to register as Agents from the public `register.html` page, as this process will be strictly handled by Admins.
- **Fixed Password UI Bug**: Resolved an issue on the register page where two conflicting password reveal "eye" icons were appearing simultaneously.
- **Cleaned Login Page**: Removed the non-functional "Keep me signed in" checkbox from `login.html`.
- **Dynamic Navbar Navigation**: Updated `base.html` so that the "Login" or "Register" buttons in the navigation bar automatically hide when the user is already on those respective pages.

**Project Browsing Experience**
- **Implemented Sorting**: Added a dynamic "Sort By" dropdown to `browse.html` and implemented backend logic in `views.py` allowing investors to sort projects by Recent, Oldest, Most/Least Investors, Highest/Lowest Expected Profit, and Highest/Lowest Target Raise.
- **Redesigned Layout**: Completely overhauled the `browse.html` UI, changing it from a grid of vertical cards to a much more scannable, data-dense horizontal list layout for easier project comparison.

**Investment UI & Logic Security**
- **Interactive Investment Slider**: Added a dynamic slider on `project_detail.html` that stays perfectly synchronized with the investment amount input box.
- **Strict Funding Caps**: Implemented backend validation in `views.py` and frontend limits to ensure an investor can never invest an amount that pushes a project past its target funding goal.
- **Input Validation**: Added Javascript to actively block users from typing minus signs (`-`), plus signs, or numbers exceeding the maximum cap into the investment input box.
- **Professional Agent Verification UI**: Redesigned the "Agent Verified" section on the investment page to use a clean, modern layout with tinted backgrounds and professional status icons instead of plain text emojis.

**Farmer Portal & Project Lifecycle**
- **Ready-to-Sell Flow**: Implemented a dedicated "Ready to Sell" button for farmers to signal when a funded project is ready to be liquidated, automatically updating the status and alerting the assigned agent.
- **Cattle Sales Requirement**: Added logic to automatically mark `CATTLE` assets as 'SOLD' when their project sale is completed. Added backend validation to block sold cattle from being reused in new projects, and updated the UI to dim sold cattle cards and display "Sold" badges.
- **Soft Delete for Assets & Projects**: Introduced an `is_deleted` field to safely "hide" assets and projects from the farmer's view without deleting the underlying historical data or agent logs. Implemented safety checks to prevent farmers from hiding active projects.

**Financial Distribution & Security**
- **Principal-First Profit Logic**: Completely refactored the backend profit distribution algorithm inside `agent_record_sale` into a dedicated `process_sale_distribution` function. The new logic guarantees investors recover 100% of their principal (Scenario A) or take the entire net revenue (Scenario B) before any profits are distributed to the farmer or platform.
- **Historical Data Migration**: Created and executed `scripts/fix_historical_sales.py` to automatically reverse the incorrect distributions for previously completed sales and migrate all users' wallet balances to strictly align with the new Principal-First mathematical model.
