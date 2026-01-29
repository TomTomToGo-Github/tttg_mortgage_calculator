# Missing future improvements

## Specify settings from Wealth Estimator
- Introduce the option to select a start date for the projection and also insert today. Raises the question if for some elements one can set different start dates? One can easily set the current income, expenses, etc. but stock income might have started in the past, so The projection should start from the current date and account for the past stock income
"projection into past AND projection into the future" -> status quo reflects current state that one can easily verify

- Add optional computation of 13.th, 14.th bonus payment for Austrian Payslip (general idea of simply having to input gross and rest is filled out automatically?)

- The hiding buttons need to be clicked twice -> correct the callback

- RSU -> currently the overshoot stock are added the first pay out -> in reality it seem to be payed out randomly one extra, or when the overshoots add up to one more stock

- Introduce categories (and subcategories) to have better overview graphs

- Introduce example months, years, etc. to gain some better educated guesses at a new years earnings/spendings.

- Fix bug of not paying back mortgage. Not a bug, but not very intuitive because the display window is smaller than the calculation. At least have a button to have both synchronour, or warning that the values are not the same

- One can import the results from the pages "stock_estimator" and "income_expenses" to the "wealth_calculator" -> it would be nice to select which settingts these pages have from the "wealth_calculator", instead of having to change pages and set them manually

- The "Savings -> Bank vs Stocks" slider and below the Sell stocks via schedule are not very intuitive yet, and are also slightly contradictory and not finetunable (one idea would be to have. Currently one would be selling all regularly and then "rebuying" the stocks). Figure out a way to treat the stock income and the buying of other stocks as separate entities (1. select the quantity of  stock income to be sold by selected schedule, then the Savings slider is applied to all income (money + money from realized stocks)).


- In wealth calculator the monthly Money Capacity and Monthly Stock Capacity are ok, but they are predefined numbers. It would be nice to additionally have some metrics like actual money realized (money + realized stock income - bought stocks) + saved money (actual money - monthly mortgage) and monthly stock gains (stock income + bought stocks - sold stocks)

- Also the slider "Savings -> Bank vs Stocks" would make sense to have there in order to easily adjust the amount of actual money available for mortgage and savings

- Rework the Overview page with the top results of the other pages

- Complete refactor of the codebase to be modular, separating computation from UI components, and make individual calculations easily understandable and editable.

- Rename presets to settings!

- Tests for the refactored codebase (primarily for the individual calculations, but also for settings of the ui?)

- Future: An optimize button -> calculating the best outcome with what you have: so much in stocks, so much money saved, etc. maybe even a LLM optimizer looking at how to reduce spending and increase income

- For now it is assumed, that nothing changes over time (apart from home appreciation and stock value increase). One could calculate more sophisticated manner, taking averages of inflation, cold progression, etc. into account