# Weekly revenue forecasting in R (forecast package), reading the DuckDB-built weekly series
suppressPackageStartupMessages({library(dplyr); library(forecast)})
raw <- read.csv("data/retail.csv", colClasses = c(Invoice = "character", StockCode = "character"))
weekly <- raw |>
  filter(Price > 0, grepl("^[0-9]{5}", StockCode)) |>
  mutate(date = as.Date(substr(InvoiceDate, 1, 10)),
         week = date - (as.integer(format(date, "%u")) - 1),
         revenue = Quantity * Price) |>
  group_by(week) |> summarise(revenue = sum(revenue), .groups = "drop") |>
  filter(week > as.Date("2009-12-01"), week < as.Date("2011-12-05"))
y <- ts(weekly$revenue, frequency = 52)
h <- 13; n <- length(y)
train <- window(y, end = time(y)[n - h]); test <- window(y, start = time(y)[n - h + 1])
cat("Weeks:", n, "\n")
fit <- auto.arima(train, D = 1, seasonal = TRUE, stepwise = TRUE)
print(fit)
fc <- forecast(fit, h = h)
snaive_fc <- snaive(train, h = h)
acc <- rbind(arima = accuracy(fc, test)["Test set", c("RMSE", "MAPE")],
             seasonal_naive = accuracy(snaive_fc, test)["Test set", c("RMSE", "MAPE")])
print(round(acc, 1))
