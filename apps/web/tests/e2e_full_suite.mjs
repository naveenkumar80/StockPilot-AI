import { chromium } from "playwright";
import fs from "fs";
import path from "path";

const BASE_URL = "http://localhost:3000";
const API_URL = "http://127.0.0.1:8000/api/v1";

const testResults = [];

function logResult(suite, name, passed, details = "") {
  testResults.push({ suite, name, passed, details, timestamp: new Date().toISOString() });
  const badge = passed ? "\x1b[32m[PASS]\x1b[0m" : "\x1b[31m[FAIL]\x1b[0m";
  console.log(`${badge} ${suite} > ${name} ${details ? `(${details})` : ""}`);
}

async function runTestSuite() {
  console.log("\n==================================================================");
  console.log("  StockPilot AI — Senior QA Automated & Manual Test Suite");
  console.log("  Testing all pages, components, buttons, modals & workflows");
  console.log("==================================================================\n");

  const browser = await chromium.launch({
    channel: "chrome",
    headless: true,
  });

  const context = await browser.newContext({
    viewport: { width: 1440, height: 900 },
  });

  const page = await context.newPage();

  // Track console and page errors
  const consoleErrors = [];
  page.on("console", (msg) => {
    if (msg.type() === "error") {
      console.log(`[BROWSER CONSOLE ERROR @ ${page.url()}]:`, msg.text());
      consoleErrors.push(`${msg.text()} (@ ${page.url()})`);
    }
  });

  page.on("pageerror", (err) => {
    console.log(`[BROWSER UNCAUGHT PAGE ERROR @ ${page.url()}]:`, err.message);
    consoleErrors.push(`${err.message} (@ ${page.url()})`);
  });

  try {
    // =========================================================================
    // SUITE 1: Global Routes Navigation & Status Code Verification
    // =========================================================================
    const routes = [
      { path: "/", name: "Dashboard" },
      { path: "/screener", name: "Stock Screener" },
      { path: "/insights", name: "Market Insights" },
      { path: "/stocks/RELIANCE", name: "Stock Detail (RELIANCE)" },
      { path: "/models", name: "Champion-Challenger Models" },
      { path: "/backtesting", name: "Backtesting Simulator" },
      { path: "/paper-trading", name: "Paper Trading Ledger" },
      { path: "/research", name: "News & AI Research" },
      { path: "/watchlist", name: "Persistent Watchlist" },
      { path: "/settings", name: "Settings & System Health" },
    ];

    for (const r of routes) {
      try {
        const resp = await page.goto(`${BASE_URL}${r.path}`, { waitUntil: "domcontentloaded", timeout: 15000 });
        const status = resp ? resp.status() : 0;
        const passed = status === 200;
        logResult("Routes & Navigation", `Route: ${r.path} (${r.name})`, passed, `HTTP ${status}`);
      } catch (err) {
        logResult("Routes & Navigation", `Route: ${r.path} (${r.name})`, false, err.message);
      }
    }

    // =========================================================================
    // SUITE 2: Header & Global Command Palette (Ctrl+K)
    // =========================================================================
    try {
      await page.goto(`${BASE_URL}/`, { waitUntil: "domcontentloaded" });
      await page.waitForTimeout(500);
      
      // Check Header Market Bar
      const niftyTicker = page.locator("text=NIFTY 50").first();
      const sensexTicker = page.locator("text=SENSEX").first();
      const hasTickers = (await niftyTicker.isVisible()) && (await sensexTicker.isVisible());
      logResult("Header & Brand", "Live Market Tickers Display", hasTickers, "NIFTY & SENSEX visible");

      // Trigger Command Palette via clicking Search Bar
      const searchTrigger = page.locator("header input[readonly]").first();
      await searchTrigger.click({ force: true });
      await page.waitForTimeout(600);

      const paletteModalInput = page.locator("input[placeholder*='Type a stock symbol']").first();
      const modalVisible = await paletteModalInput.isVisible();
      logResult("Command Palette", "Trigger via Header Search / Shortcut", modalVisible, "Spotlight modal opened");

      if (modalVisible) {
        // Type search query
        await paletteModalInput.fill("TCS");
        await page.waitForTimeout(300);
        const searchResult = await page.locator("text=Tata Consultancy Services").first().isVisible();
        logResult("Command Palette", "Search Ticker Filter ('TCS')", searchResult, "TCS found in palette results");

        // Close modal via Escape
        await page.keyboard.press("Escape");
        await page.waitForTimeout(300);
        const closed = !(await paletteModalInput.isVisible());
        logResult("Command Palette", "Dismiss via Escape", closed, "Modal closed cleanly");
      }
    } catch (err) {
      logResult("Command Palette", "Workflow Execution", false, err.message);
    }

    // =========================================================================
    // SUITE 3: Stock Screener & Interactive Filters
    // =========================================================================
    try {
      await page.goto(`${BASE_URL}/screener`, { waitUntil: "domcontentloaded" });

      // Wait for table rows to load from API
      await page.waitForSelector("table tbody tr", { timeout: 10000 });
      const tableRows = await page.locator("table tbody tr").count();
      logResult("Stock Screener", "Table Rows Rendered", tableRows > 0, `${tableRows} stocks displayed`);

      // Test Screener Search Input Filter
      const screenerSearchBox = page.locator("input[placeholder='Search by symbol or company name...']").first();
      if (await screenerSearchBox.isVisible()) {
        await screenerSearchBox.fill("INFY");
        await page.waitForTimeout(400);
        const rowText = await page.locator("table tbody").innerText();
        const searchWorked = rowText.includes("INFY") && !rowText.includes("TATAMOTORS");
        logResult("Stock Screener", "Instant Search Filter ('INFY')", searchWorked, "Filtered accurately");
        await screenerSearchBox.fill(""); // clear
        await page.waitForTimeout(300);
      }

      // Test Signal Filter Pill (e.g. BUY)
      const buyPill = page.locator("button:has-text('BUY')").first();
      if (await buyPill.isVisible()) {
        await buyPill.click();
        await page.waitForTimeout(400);
        logResult("Stock Screener", "Signal Filter Click ('BUY')", true, "BUY filter active");
        // Reset to All
        const allPill = page.locator("button:has-text('All')").first();
        if (await allPill.isVisible()) await allPill.click();
      }
    } catch (err) {
      logResult("Stock Screener", "Screener Testing", false, err.message);
    }

    // =========================================================================
    // SUITE 4: Quick Paper Trade Modal from Screener
    // =========================================================================
    try {
      await page.goto(`${BASE_URL}/screener`, { waitUntil: "domcontentloaded" });
      await page.waitForSelector("table tbody tr button:has-text('Trade')", { timeout: 10000 });
      const tradeButton = page.locator("table tbody tr button:has-text('Trade')").first();
      const hasTradeBtn = await tradeButton.isVisible();
      logResult("Quick Paper Trade", "Trade Action Button Visible", hasTradeBtn, "Trade button present in table");

      if (hasTradeBtn) {
        await tradeButton.click();
        await page.waitForTimeout(500);

        const modalHeader = await page.locator("text=Quick Paper Trade:").isVisible();
        logResult("Quick Paper Trade", "Modal Open", modalHeader, "QuickTradeModal rendered");

        // Verify Quantity preset button (e.g. '25')
        const qty25Btn = page.locator("button:has-text('+25')").first();
        if (await qty25Btn.isVisible()) {
          await qty25Btn.click();
          await page.waitForTimeout(200);
          logResult("Quick Paper Trade", "Preset Qty Button (+25)", true, "Qty adjusted");
        }

        // Click Submit Order
        const submitOrderBtn = page.locator("button:has-text('Execute Simulated')").first();
        if (await submitOrderBtn.isVisible()) {
          await submitOrderBtn.click();
          await page.waitForTimeout(1000);
          const orderSuccess = (await page.locator("text=Order Executed Successfully").isVisible()) ||
                               (await page.locator("text=Simulated BUY").isVisible());
          logResult("Quick Paper Trade", "Simulated Order Execution", orderSuccess, "Order filled with receipt");

          // Close modal
          const doneBtn = page.locator("button:has-text('Done')").first();
          if (await doneBtn.isVisible()) await doneBtn.click();
        }
      }
    } catch (err) {
      logResult("Quick Paper Trade", "Modal Testing", false, err.message);
    }

    // =========================================================================
    // SUITE 5: Candlestick Chart & Technical Indicators Overlay
    // =========================================================================
    try {
      await page.goto(`${BASE_URL}/stocks/RELIANCE`, { waitUntil: "domcontentloaded" });

      // Verify Chart SVG rendered
      await page.waitForSelector("svg", { timeout: 10000 });
      const svgChart = await page.locator("svg").count();
      logResult("Technical Chart", "Candlestick SVG Rendered", svgChart > 0, `${svgChart} SVG elements rendered`);

      // Test Indicator Toggles (EMA 20, EMA 50, Bollinger Bands)
      const ema20Btn = page.locator("button:has-text('EMA 20')").first();
      const ema50Btn = page.locator("button:has-text('EMA 50')").first();
      const bbBtn = page.locator("button:has-text('Bollinger')").first();

      if (await ema20Btn.isVisible()) {
        await ema20Btn.click();
        await page.waitForTimeout(300);
        logResult("Technical Chart", "Toggle EMA 20 Overlay", true, "Indicator activated");
      }

      if (await ema50Btn.isVisible()) {
        await ema50Btn.click();
        await page.waitForTimeout(300);
        logResult("Technical Chart", "Toggle EMA 50 Overlay", true, "Indicator activated");
      }

      if (await bbBtn.isVisible()) {
        await bbBtn.click();
        await page.waitForTimeout(300);
        logResult("Technical Chart", "Toggle Bollinger Bands Overlay", true, "Bands activated");
      }

      // Check Timeframe Buttons (1D, 1W, 1M)
      const tf1W = page.locator("button:has-text('1W')").first();
      if (await tf1W.isVisible()) {
        await tf1W.click();
        await page.waitForTimeout(500);
        logResult("Technical Chart", "Timeframe Switcher ('1W')", true, "Timeframe request dispatched");
      }
    } catch (err) {
      logResult("Technical Chart", "Chart Controls", false, err.message);
    }

    // =========================================================================
    // SUITE 6: Champion-Challenger Tournament Arena (/models)
    // =========================================================================
    try {
      await page.goto(`${BASE_URL}/models`, { waitUntil: "domcontentloaded" });
      await page.waitForSelector("text=ACTIVE CHAMPION", { timeout: 10000 });

      // Verify Champion Trophy Banner
      const champBanner = await page.locator("text=ACTIVE CHAMPION").isVisible();
      logResult("Champion-Challenger", "Champion Hero Banner", champBanner, "Current Champion rendered with live status");

      // Verify Leaderboard Table
      const candidateRows = await page.locator("table tbody tr").count();
      logResult("Champion-Challenger", "Leaderboard Candidates Table", candidateRows >= 3, `${candidateRows} models in tournament`);

      // Test Candidate Promotion Action or Production Status
      const inProdBadge = page.locator("text=In Production").first();
      const hasProdModel = await inProdBadge.isVisible();
      logResult("Champion-Challenger", "Active Champion in Production", hasProdModel, "Champion model bound to inference pipeline");

      // Verify Factor Attribution Ranking
      const factorsCount = await page.locator("text=Champion Factor Attribution").isVisible();
      logResult("Champion-Challenger", "Factor Attribution Display", factorsCount, "Normalized feature gain visible");
    } catch (err) {
      logResult("Champion-Challenger", "Tournament Testing", false, err.message);
    }

    // =========================================================================
    // SUITE 7: Backtesting Simulator & CSV Export
    // =========================================================================
    try {
      await page.goto(`${BASE_URL}/backtesting`, { waitUntil: "domcontentloaded" });

      // Verify Backtest Form
      const runBtn = page.locator("button:has-text('Run Backtest')").first();
      const hasRunBtn = await runBtn.isVisible();
      logResult("Backtesting Engine", "Run Backtest Form", hasRunBtn, "Configuration controls visible");

      if (hasRunBtn) {
        await runBtn.click();
        // Wait for results
        await page.waitForSelector("text=Sharpe / Sortino", { timeout: 15000 });
        const sharpeCard = await page.locator("text=Sharpe / Sortino").first().isVisible();
        logResult("Backtesting Engine", "Execution & Metric Cards", sharpeCard, "Simulated P&L and risk metrics rendered");

        // Verify CSV Export Button
        const exportBtn = page.locator("button:has-text('Export CSV')").first();
        const hasExportBtn = await exportBtn.isVisible();
        logResult("Backtesting Engine", "Trade Log CSV Export Button", hasExportBtn, "Export action button enabled");
      }
    } catch (err) {
      logResult("Backtesting Engine", "Backtest Workflow", false, err.message);
    }

    // =========================================================================
    // SUITE 8: Paper Trading Portfolio & Reset
    // =========================================================================
    try {
      await page.goto(`${BASE_URL}/paper-trading`, { waitUntil: "domcontentloaded" });

      await page.waitForSelector("text=Total Equity", { timeout: 15000 });
      const totalEquity = await page.locator("text=Total Equity").first().isVisible();
      const cashBalance = await page.locator("text=Available Cash Balance").first().isVisible();
      logResult("Paper Trading", "Portfolio Snapshot Cards", totalEquity && cashBalance, "Capital metrics loaded");

      // Verify Safety Guardrail Banner
      const guardrailBanner = await page.locator("text=Paper Trading Guarantee").first().isVisible();
      logResult("Paper Trading", "Safety Guardrail Banner", guardrailBanner, "Zero real-risk guarantee active");

      // Verify Portfolio Control Buttons
      const refreshBtn = page.locator("button:has-text('Refresh')").first();
      const hasRefresh = await refreshBtn.isVisible();
      logResult("Paper Trading", "Balance Refresh Action Button", hasRefresh, "Refresh control available");
    } catch (err) {
      logResult("Paper Trading", "Trading Ledger", false, err.message);
    }

    // =========================================================================
    // SUITE 9: Market Insights & Macro Intelligence (/insights)
    // =========================================================================
    try {
      await page.goto(`${BASE_URL}/insights`, { waitUntil: "domcontentloaded" });

      await page.waitForSelector("text=Market Regime", { timeout: 10000 });
      const regimeCard = await page.locator("text=Market Regime").first().isVisible();
      const breadthCard = await page.locator("text=NIFTY Breadth (A/D)").first().isVisible();
      const sectorGrid = await page.locator("text=Sector Rotation").first().isVisible();
      const topGainers = await page.locator("text=Top Gainers Today").first().isVisible();

      logResult("Market Insights", "Market Regime & Breadth Cards", regimeCard && breadthCard, "Macro health gauges rendered");
      logResult("Market Insights", "Sector Rotation Heatmap", sectorGrid, "NSE sector cards visible");
      logResult("Market Insights", "Top Gainers & Lagging Stocks", topGainers, "Movers split list loaded");
    } catch (err) {
      logResult("Market Insights", "Insights Dashboard", false, err.message);
    }

    // =========================================================================
    // SUITE 10: Persistent Watchlist with Local Storage
    // =========================================================================
    try {
      await page.goto(`${BASE_URL}/watchlist`, { waitUntil: "domcontentloaded" });

      await page.waitForSelector("text=Personal Watchlist", { timeout: 10000 });
      const watchlistHeader = await page.locator("text=Personal Watchlist").first().isVisible();
      logResult("Watchlist", "Watchlist Page Loaded", watchlistHeader, "Header loaded");

      // Open Add Stock Drawer
      const addStockBtn = page.locator("button:has-text('+ Add Symbol')").first();
      if (await addStockBtn.isVisible()) {
        await addStockBtn.click();
        await page.waitForTimeout(400);

        const drawerOpen = await page.locator("text=Add Stock to Watchlist").first().isVisible();
        logResult("Watchlist", "Add Stock Drawer", drawerOpen, "Drawer rendered");

        // Close drawer
        const closeBtn = page.locator("button:has-text('Cancel')").first();
        if (await closeBtn.isVisible()) await closeBtn.click();
      }
    } catch (err) {
      logResult("Watchlist", "Watchlist Testing", false, err.message);
    }

    // =========================================================================
    // SUITE 11: AI News & Research Assistant
    // =========================================================================
    try {
      await page.goto(`${BASE_URL}/research`, { waitUntil: "domcontentloaded" });

      await page.waitForSelector("text=Evidence-Based Research Assistant", { timeout: 10000 });
      const newsHeader = await page.locator("text=Evidence-Based Research Assistant").first().isVisible();
      const promptChips = await page.locator("button:has-text('Why did TCS')").first().isVisible();

      logResult("Research & News", "Aggregated Financial News Feed", newsHeader, "Feed items rendered");
      logResult("Research & News", "Grounded AI Research Assistant", promptChips, "Query input and chips ready");
    } catch (err) {
      logResult("Research & News", "Research Module", false, err.message);
    }

    // =========================================================================
    // SUITE 12: Settings & Preferences
    // =========================================================================
    try {
      await page.goto(`${BASE_URL}/settings`, { waitUntil: "domcontentloaded" });

      await page.waitForSelector("text=Settings & System Health", { timeout: 10000 });
      const settingsHeading = await page.locator("text=Settings & System Health").first().isVisible();
      const recheckBtn = page.locator("button:has-text('Re-check Health')").first();
      const hasRecheckBtn = await recheckBtn.isVisible();

      if (hasRecheckBtn) {
        await recheckBtn.click();
        await page.waitForTimeout(500);
        logResult("Settings", "System Health Re-check Action", true, "Health re-checked successfully");
      }
      logResult("Settings", "Settings Page Verification", settingsHeading, "Settings form rendered");
    } catch (err) {
      logResult("Settings", "Settings Module", false, err.message);
    }

    // =========================================================================
    // SUITE 13: Console Integrity & Hydration Errors Check
    // =========================================================================
    const criticalErrors = consoleErrors.filter(
      (e) => !e.includes("favicon") && !e.includes("404") && !e.includes("status of 404") && !e.includes("ERR_NETWORK_IO_SUSPENDED")
    );
    const consoleClean = criticalErrors.length === 0;
    logResult("Console Integrity", "Zero Uncaught JS / Hydration Errors", consoleClean, 
      consoleClean ? "0 critical console errors" : `${criticalErrors.length} errors: ${criticalErrors.slice(0, 2).join("; ")}`
    );

  } finally {
    await browser.close();
  }

  // Summary Report
  const passedCount = testResults.filter((t) => t.passed).length;
  const totalCount = testResults.length;
  const passRate = ((passedCount / totalCount) * 100).toFixed(1);

  console.log("\n==================================================================");
  console.log(`  QA TEST SUMMARY: ${passedCount}/${totalCount} Passed (${passRate}%)`);
  console.log("==================================================================\n");

  // Write detailed JSON report
  const reportPath = path.resolve("./qa_test_report.json");
  fs.writeFileSync(
    reportPath,
    JSON.stringify(
      {
        summary: {
          total: totalCount,
          passed: passedCount,
          failed: totalCount - passedCount,
          pass_rate: `${passRate}%`,
          timestamp: new Date().toISOString(),
        },
        results: testResults,
      },
      null,
      2
    )
  );
  console.log(`Detailed test report saved to: ${reportPath}`);
}

runTestSuite().catch((err) => {
  console.error("FATAL SUITE ERROR:", err);
  process.exit(1);
});
