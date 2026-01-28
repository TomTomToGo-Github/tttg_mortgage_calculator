# Missing future improvements

## Specify settings from Wealth Estimator
- One can import the results from the pages "stock_estimator" and "income_expenses" to the "wealth_calculator" -> it would be nice to select which settingts these pages have from the "wealth_calculator", instead of having to change pages and set them manually

- The "Savings -> Bank vs Stocks" slider and below the Sell stocks via schedule are not very intuitive yet, and are also slightly contradictory and not finetunable (one idea would be to have. Currently one would be selling all regularly and then "rebuying" the stocks). Figure out a way to treat the stock income and the buying of other stocks as separate entities (1. select the quantity of  stock income to be sold by selected schedule, then the Savings slider is applied to all income (money + money from realized stocks)).

- Load settings in "Income & Expenses" has a "Select ..." include this in the others, or leave it out everywhere - potentially also load the setting that is displayed right away during startup

- In wealth calculator the monthly Money Capacity and Monthly Stock Capacity are ok, but they are predefined numbers. It would be nice to additionally have some metrics like actual money realized (money + realized stock income - bought stocks) + saved money (actual money - monthly mortgage) and monthly stock gains (stock income + bought stocks - sold stocks)

- Also the slider "Savings -> Bank vs Stocks" would make sense to have there in order to easily adjust the amount of actual money available for mortgage and savings

- Rework the Overview page with the top results of the other pages

- Complete refactor of the codebase to be modular, separating computation from UI components, and make individual calculations easily understandable and editable