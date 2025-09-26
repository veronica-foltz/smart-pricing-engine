Smart Pricing Engine 💰

A full-stack pricing optimization tool that helps small businesses set smarter prices by analyzing demand, competitor benchmarks, and inventory levels.

Problem

  - Most small retailers and cafés set prices manually, often:

     - Leaving money on the table when demand is high, or

     - Overpricing when stock is high and competitors undercut them.

  - Managers need a simple way to:

      See where prices could move,

      Understand expected profit impact, and

      Apply changes quickly without spreadsheets.

Solution

Smart Pricing Engine ingests:

  Product catalog (name, category, cost, price)

  Sales history

  Inventory levels

  Competitor prices

It then:

  Runs a rules-based + data-driven engine to generate recommended prices.

  Shows the expected profit delta for each product.

  Flags inventory conditions (low, normal, high).

  Provides an interactive dashboard for managers to simulate “what if” scenarios.

Features

  - Interactive Dashboard (HTML/JS frontend)

  - Run pricing recommendations at the click of a button

  - Search & filter products by category

  - Color-coded profit delta (+/-)

  - KPI cards (uplift, price changes, average margin)

  - Profit vs Price curve visualization

Tech Stack

  - Backend: FastAPI, Pandas, Uvicorn

  - Frontend: HTML, CSS, Vanilla JS (no frameworks needed)

  - Data: CSV seed datasets (easily replaceable with real data feeds)
