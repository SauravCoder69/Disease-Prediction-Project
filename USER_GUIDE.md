# 📱 MEDICAL REPORT ANALYZER - USER GUIDE

## Quick Start

### Step 1: Login/Create Account
```
Sidebar Menu:
├─ Username: Enter your username
├─ Password: Enter password  
└─ Login or Create Account button
```

### Step 2: Navigate to Report Analyzer
```
Sidebar Menu → Select "Report Analyzer"
```

### Step 3: Upload or Paste Report
```
Option A: Upload File
├─ Formats: PDF, JPG, PNG, TXT
├─ Max Size: 15 MB
└─ Click file uploader

Option B: Paste Text
├─ Copy lab report text
├─ Paste in text area
└─ Leave file uploader empty
```

### Step 4: Click "Analyze Report"
```
Progress shows:
✓ Validating file...
✓ Extracting text from file...
✓ Parsing lab values...
✓ Complete!
```

### Step 5: Review Results
```
Results Display:
├─ Extracted text preview
├─ Lab parameters (metric cards)
├─ Detailed results (color-coded)
├─ Health summary
└─ Medical disclaimer
```

---

## 📊 EXPECTED RESULTS

### Sample Input:
```
BLOOD TEST REPORT
Date: May 10, 2024
Patient: John Doe

Results:
Hemoglobin: 13.5 g/dL
WBC: 7.2 x10^3/uL
RBC: 4.8 x10^6/uL
Platelet Count: 250 x10^3/uL
Blood Pressure: 120/80 mmHg
Glucose (Fasting): 95 mg/dL
Total Cholesterol: 185 mg/dL
LDL Cholesterol: 110 mg/dL
HDL Cholesterol: 50 mg/dL
Triglycerides: 130 mg/dL
```

### Expected Output:
```
✅ Analysis Complete!

METRICS:
┌─────────────────────────────────┐
│ Hemoglobin (Hb)                 │
│ 13.5 g/dL                       │
│ Status: NORMAL ✓                │
│ Within broad adult range         │
└─────────────────────────────────┘

┌─────────────────────────────────┐
│ LDL Cholesterol                 │
│ 110 mg/dL                       │
│ Status: HIGH ⚠️                 │
│ Borderline high LDL             │
└─────────────────────────────────┘

... (9 parameters total)

HEALTH SUMMARY:
Parsed 10 lab parameter(s) from the document.
Values outside demo reference bands: LDL (High), BP (High).
Discuss findings with a qualified clinician.
Verify all results with your clinician and official lab report.
```

---

## 🎨 COLOR CODING

### Status Indicators:
```
🟢 GREEN - Normal
   ├─ Within demo reference range
   └─ No action needed

🔴 RED - High
   ├─ Above demo reference range
   └─ Discuss with clinician

🟠 ORANGE - Low
   ├─ Below demo reference range
   └─ Discuss with clinician

⚫ GRAY - Unknown
   ├─ Unable to determine status
   └─ Verify with clinician
```

---

## 📋 SUPPORTED LAB PARAMETERS

### Complete List:

1. **Blood Glucose / Sugar**
   - Accepts: Glucose, Fasting Glucose (FBS), Random Blood Sugar (RBS)
   - Units: mg/dL, mmol/L (auto-converted)
   - Status: Normal < 100 mg/dL (fasting)

2. **Hemoglobin (Hb)**
   - Accepts: Hemoglobin, Hgb, HG
   - Units: g/dL, g/L
   - Status: Normal 12.0-17.5 g/dL

3. **White Blood Cells (WBC)**
   - Accepts: WBC, White Blood Cell Count, TLC
   - Units: x10³/uL, /uL, /mm³
   - Status: Normal 4.5-11.0 x10³/uL

4. **Red Blood Cells (RBC)**
   - Accepts: RBC, Red Blood Cell Count
   - Units: x10⁶/uL, /uL
   - Status: Normal 4.0-5.9 x10⁶/uL

5. **Platelets**
   - Accepts: Platelet, Plt, Platelet Count
   - Units: x10³/uL, /uL, /mm³
   - Status: Normal 150-450 x10³/uL

6. **Blood Pressure (BP)**
   - Accepts: BP, Blood Pressure
   - Format: XXX/YYY mmHg
   - Status: Normal < 120/80 mmHg

7. **Total Cholesterol**
   - Accepts: Total Cholesterol, Cholesterol
   - Units: mg/dL
   - Status: Normal < 200 mg/dL

8. **LDL Cholesterol** ⭐ NEW
   - Accepts: LDL, Bad Cholesterol
   - Units: mg/dL
   - Status: Optimal < 100 mg/dL

9. **HDL Cholesterol** ⭐ NEW
   - Accepts: HDL, Good Cholesterol
   - Units: mg/dL
   - Status: Adequate > 40 mg/dL

10. **Triglycerides** ⭐ NEW
    - Accepts: Triglyceride, Triglycerides
    - Units: mg/dL
    - Status: Normal < 150 mg/dL

---

## 🔧 SUPPORTED FILE FORMATS

### PDFs:
- ✅ Text-based PDFs (extracted directly)
- ✅ Scanned PDFs (OCR processed)
- ✅ Mixed PDFs (text + scanned pages)
- ❌ Password-protected PDFs

### Images:
- ✅ JPG / JPEG
- ✅ PNG
- ✅ TIF / TIFF
- ✅ BMP
- ✅ WebP

### Text:
- ✅ Plain text (.txt)
- ✅ CSV (.csv)
- ✅ Markdown (.md)
- ✅ Pasted text

### File Limits:
- Max size: 15 MB
- Max text length: 400,000 characters
- Max PDF pages to OCR: 25

---

## ⏱️ PROCESSING TIMES

### Typical Scenarios:

```
Text-based PDF (2 pages):
Time: 2-3 seconds
Process: Extract text directly
Result: Fast, high accuracy

Scanned PDF (3 pages):
Time: 5-8 seconds
Process: Convert to images → OCR
Result: Good accuracy if clear scan

JPG Lab Report:
Time: 3-5 seconds (Tesseract)
Time: 5-10 seconds (EasyOCR)
Result: Depends on image clarity

First EasyOCR Run:
Time: 30-60 seconds
Process: Download models (~100MB+)
Result: ONE-TIME ONLY, subsequent runs < 5 sec

Text Paste:
Time: < 1 second
Process: Parse directly
Result: Instant results
```

---

## 🛠️ TROUBLESHOOTING

### Problem: "No text found in PDF"
```
Possible Causes:
1. PDF is password-protected
2. Scanned image quality too low
3. File is corrupted
4. PDF contains only images/graphics

Solutions:
• Try another PDF file
• Ensure scan is high-resolution (300+ DPI)
• Copy text from original report and paste
• Check file integrity (open with PDF viewer)
```

### Problem: OCR takes 30-60 seconds on first use
```
Reason:
EasyOCR downloading models (~100MB+) - NORMAL

Solutions:
• Wait for first-time download (subsequent runs faster)
• Or install Tesseract for instant OCR (optional)
• https://github.com/UB-Mannheim/tesseract/wiki
```

### Problem: Parsing finds no lab parameters
```
Possible Causes:
1. Lab names don't match expected patterns
2. OCR quality too poor to read clearly
3. Units not recognized
4. Values unclear/blurry in scan

Solutions:
• Try a clearer/higher-resolution scan
• Paste specific lab lines (e.g., "Hemoglobin: 13.5 g/dL")
• Check spelling matches report (e.g., "Hb" vs "Hemoglobin")
• Use standard units (mg/dL, g/dL, etc.)
```

### Problem: File upload fails
```
Possible Causes:
1. File size > 15 MB
2. File format not supported
3. Browser cache issue

Solutions:
• Check file size (max 15 MB)
• Use supported format (PDF, JPG, PNG, TXT)
• Clear browser cache
• Try pasting text instead
```

### Problem: Results showing as "Unknown" status
```
Reason:
Value not recognized or outside demo range

Solutions:
• Check units are correct
• Verify value was extracted correctly
• See extracted text preview
• Consult clinician for proper interpretation
```

---

## 📝 BEST PRACTICES

### For Best Results:

1. **Scanned PDFs:**
   - Use high-resolution scans (300+ DPI)
   - Ensure good lighting in images
   - Black text on white background ideal
   - Minimize skew/rotation

2. **JPG/PNG Images:**
   - Clear, high-contrast images
   - Avoid shadows and glare
   - Portrait orientation preferred
   - Full lab report visible

3. **Text Input:**
   - Copy directly from lab report
   - Include one lab value per line
   - Use standard abbreviations (Hb, WBC, etc.)
   - Include units (mg/dL, g/dL, etc.)

4. **Ambiguous Values:**
   - Include context (e.g., "Fasting Glucose")
   - Specify units clearly
   - Use full names if unsure
   - Copy from official report

---

## ⚠️ IMPORTANT DISCLAIMERS

### NOT a Medical Device:
- 🚫 Cannot be used for diagnosis
- 🚫 Cannot replace clinical assessment
- 🚫 Cannot substitute for professional interpretation

### Demo Reference Ranges:
- Ranges are educational only
- Vary by age, gender, laboratory
- Not suitable for all populations
- Individual factors affect normal ranges

### Always Consult:
- Qualified healthcare professional
- Your personal doctor/clinician
- Official lab report interpretation
- For any medical decisions

### Data Privacy:
- All processing happens locally
- No data sent to external servers
- No data stored permanently
- Session-only in-memory storage

---

## 🎓 REFERENCE INFORMATION

### Understanding Results:

**NORMAL Status:**
- Value within demo reference range
- No immediate action needed
- Consult clinician if concerned
- Verify with official report

**HIGH Status:**
- Value above demo reference range
- May indicate elevated levels
- Discuss with healthcare provider
- Follow up as recommended

**LOW Status:**
- Value below demo reference range
- May indicate deficiency
- Discuss with healthcare provider
- May need supplementation/treatment

**UNKNOWN Status:**
- Could not determine status
- Value outside parsing patterns
- May need manual review
- Consult clinician for interpretation

---

## 💡 TIPS & TRICKS

### Tip 1: Batch Processing
If analyzing multiple reports:
1. Open each report separately
2. Note down parsed values
3. Compile for trends
4. Discuss with clinician

### Tip 2: Compare Over Time
Many labs provide historical data:
1. Upload each report separately
2. Track parameter trends
3. Look for improvement/decline
4. Share trend info with doctor

### Tip 3: Print Results
The app's results can be:
1. Screenshotted
2. Shared with clinician
3. Added to medical records
4. Used for reference

### Tip 4: Mix & Match
For clearer results:
1. Paste text for sure values
2. Upload PDF for comprehensive
3. Use both for accuracy
4. Cross-reference results

---

## 🆘 GETTING HELP

### Check:
1. **Extracted Text Preview** - See what was extracted
2. **Troubleshooting Section** - Find common solutions
3. **Console Logs** - Debug information (for developers)
4. **Documentation** - REPORT_ANALYZER_FIX_SUMMARY.md

### Installation Issues:
```bash
# Reinstall all dependencies
pip install --upgrade -r requirements.txt

# For Tesseract (optional):
# Windows: https://github.com/UB-Mannheim/tesseract/wiki
```

### Feature Requests:
The system supports:
- 10+ standard lab parameters
- Multiple file formats
- Advanced OCR
- Automatic unit conversion
- Status determination

---

## 🎯 QUICK SUMMARY

| Feature | Support |
|---------|---------|
| PDF Upload | ✅ Yes |
| Image Upload | ✅ Yes |
| Text Paste | ✅ Yes |
| Scanned Docs | ✅ Yes |
| OCR Processing | ✅ Yes |
| Lab Parsing | ✅ 10+ params |
| Status Determination | ✅ Yes |
| Progress Indication | ✅ Yes |
| Error Recovery | ✅ Yes |
| Medical Disclaimer | ✅ Yes |

---

**Last Updated:** May 13, 2026
**Version:** 2.0
**Status:** Production Ready ✅
