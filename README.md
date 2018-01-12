# ₿ Coinbin.org

### The Human–Friendly API Service for Crypto Currency Information.

This free web service exists to provide information on "coins". Supports all crypto–currencies.

### Example API Endpoints

`$ curl https://coinbin.org/lbc`

```json
{
  "coin": {
    "name": "LBRY Credits", 
    "rank": "100", 
    "ticker": "lbc", 
    "value": 0.429737, 
    "value.currency": "USD"
  }
}
```
      

`$ curl https://coinbin.org/lbc/42.01`

```json
{
  "coin": {
    "exchange_rate": 0.429737, 
    "value": 18.053251369999998, 
    "value.currency": "USD"
  }
}
```
      

`$ curl https://coinbin.org/lbc/to/sc`

```
{
  "coin": {
    "exchange_rate": 61.98696034733942
  }
}
```
      

`$ curl https://coinbin.org/lbc/42.01/to/sc`

```json
{
  "coin": {
    "exchange_rate": 61.98696034733942, 
    "value": 2604.072204191729, 
    "value.coin": "sc"
  }
}
```

`$ curl https://coinbin.org/lbc/history`

```json
{
  "history": [
    {
      "timestamp": "2017-08-24T04:00:55.932092Z",
      "value": 0.3404,
      "value.currency": "USD",
      "when": "today"
    }, ...

... {
      "timestamp": "2016-07-12T04:01:09.167162Z",
      "value": 0.239634,
      "value.currency": "USD",
      "when": "Jul 12 2016"
    }
  ]
}
```

## More Resources

- [Awesome Crypto Currency Tools & Algorithms (Guide)](https://github.com/kennethreitz/awesome-coins)
