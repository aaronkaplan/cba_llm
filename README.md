# cba_llm
proof of concept multi-lingual RAG and LLM system for CBA / displayeurope.eu


# Overview


## tokens.py

Example how to calculate the number of tokens for openai models and anthropic

## Result of the estimation

We estimated the number of tokens for openai (tiktoken) 
for both the "Transcripts" table and the "ContentItems"(content column)
For this method we sampled 100 random postgresql rows.


Result:

### Transcripts:
```
count    100.000000
mean    7682.840000
std     5185.550545
min      581.000000
25%     4276.000000
50%     6776.000000
75%    10303.250000
max    27433.000000
```

### ContentItems

```
            Tokens
count   101.000000
mean    311.277228
std     339.309125
min       8.000000
25%      92.000000
50%     193.000000
75%     434.000000
max    2138.000000
```

If we calculate that for OpenAI (tiktoken) for using the gpt-3.5-trubo model (see [princing](https://openai.com/pricing)) page), we will need 

gpt-3.5-turbo-0125	$0.50 / 1M tokens	$1.50 / 1M tokens

Example calc for contentItems:
$$$
311,277228 (average contentitem tokens) * 1000 (articles) /10^6*2  (price per 1 million tokens input + output)
$$$

So, for 1000 articles (for the PoC demo), we will need in average:
| Price     | Description                                        |
|-----------|----------------------------------------------------|
| 15 USD    | for 1000 articles (transcripts table)              |
| 0.62 USD  | for 1000 articles (contentitems (content) table)   |



So, for 1000 articles (for the PoC demo), we will need in average:
| Price     | Description                                        |
|-----------|----------------------------------------------------|
| 11.52     | for 1000 articles (transcripts table)              |
| 0.47 USD  | for 1000 articles (contentitems (content) table)   |




