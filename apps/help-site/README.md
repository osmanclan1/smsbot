# Oakton Alert – Help / Support site

Static help page for the Oakton Alert SMS service. Host this folder (or its built output) at the URL you use in your help message.

## SMS help message (copy)

Use this in your automated messages (e.g. after sending an alert):

```
[Oakton Alert] For assistance with your tuition balance or this automated service, please visit (website) or email (Your Support Email). Reply STOP to opt out.
```

Replace:
- **(website)** → full URL to this page (e.g. `https://yoursite.com/help` or `https://www.oakton.edu/alert-help`)
- **(Your Support Email)** → your real support address (e.g. `studentaccounts@oakton.edu`)

## What to edit before going live

1. **Support email**  
   In `index.html`, update the contact section:
   - Change `support@oakton.edu` to your actual support email (both in the `mailto:` link and the visible text).

2. **Oakton.edu link**  
   The “Go to Oakton.edu” button points to `https://www.oakton.edu`. Change the `href` if you want a specific page (e.g. payment portal).

3. **Footer / contact note**  
   Remove or edit the line that says “Replace with your actual support email before going live” once the real email is in place.

## Run locally

Serve the folder with any static server, for example:

```bash
# From project root
cd apps/help-site
npx serve .
# or
python3 -m http.server 8080
```

Then open `http://localhost:8080` (or the URL shown by `serve`).

## Deploy

- Upload the contents of `apps/help-site/` to any static host (S3 + CloudFront, Netlify, Vercel, GitHub Pages, etc.).
- Use the resulting URL as **(website)** in the SMS help message above.

No build step is required; `index.html` and `styles.css` are ready to deploy as-is.
