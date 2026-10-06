# Day 1 Lab: Answers

Name:

## 1. Leakage
Which columns did you drop and why? Is `tsunami` leaky? Is `magType`?

I dropped `title`, `sig`, `mmi`, `cdi`, `felt` and `alert`. `title` contains the magnitude as text ("M 0.1 - 8 km WNW of Idyllwild, CA") and `sig` is computed from it (correlation with `mag` 0.93 in my `all_week` pull). `mmi`, `cdi`, `felt` and `alert` are filled in after the event from shaking reports and impact assessments, so I would not have them at prediction time; they are 95–99% empty and simply being filled gives the answer away (12 of the 13 events with an `alert` were big quakes). `mag` itself is removed from X in `split_data` and kept in the saved CSV only as the Day 3 target.

`tsunami` is leaky in principle, because the flag is set after the size and location are assessed. In my pull it was 0 for all 1,843 events, so it carried no information either way, and I left it out of the features. `magType` is leaky: the method is chosen according to how large the event is. All 18 `mww` events were big, while none of the 1,660 `ml` and `md` events were, so a model could read the label straight from it. I left it out as well.

## 2. Stream vs batch
How many events changed (same `id`, newer `updated`) during your stream window? What does that tell you about "latest version wins"?


## 3. Outliers
Your decision on negative depth and negative magnitude, with reasoning.

I kept both. Negative depth (69 events, lowest −3.29 km) means the event was above the reference level; 54 of the 69 came from the Hawaii and Alaska volcano networks (`hv`, `av`), where quakes occur inside the mountain above sea level. Negative magnitude (91 events, lowest −1.22) is also real: the scale is logarithmic, so very small events recorded by dense local networks fall below zero; 80 of the 91 came from `av`.

The IQR mask is not a safe delete rule here. On `mag` it flags 190 events, and 180 of them are on the high side, including all 118 big quakes, so dropping "outliers" would remove the entire positive class. On `depth_km` it flags 273 deep events and none of the negative ones. I use the mask only to inspect the data and rely on the robust scaler to handle the long tails.

## 4. Cardinality
You grouped `region` to top-k. Name one alternative encoding and one risk it carries.

`region` had 73 distinct values in my pull and 25 of them appeared only once, so one-hot encoding it directly would add 73 mostly empty columns, and new regions would keep appearing in later data. Keeping the top 15 plus "Other" gives 16 columns.

An alternative is target encoding: replace each region with the share of big quakes seen in that region. It needs only one column, but it carries a leakage and overfitting risk. A region seen once gets a value of exactly 0 or 1, which is the label itself, so the encoding must be fitted on the training fold only and smoothed towards the overall rate.
