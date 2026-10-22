# Damage Report

[Español](README.md) | [English](README.en.md)

**Challenge 1 · Forensics · Difficulty: easy**

## Challenge

A file named `incident_report_BmulVGm.pdf` is received. According to the challenge statement, it looks like a normal PDF, but viewers reported that its signature was incorrect. The goal was to recover whatever was inside the file without trusting its name or extension.

> "Here is the incident report. The file name and container suggest that it is a normal PDF document, but all viewers report an incorrect signature.
>
> Treat the artifact as evidence, not as reliable metadata, and recover everything that was included in it before the export became corrupted."

[File](incident_report_BmulVGm.pdf)

## Solution

1. Rename `incident_report_BmulVGm.pdf` to `incident_report_BmulVGm.zip`.
2. Extract the ZIP.
3. Open `flag.txt`.

Examining the file confirmed that it does not contain the `%PDF-` header and that it has a ZIP structure starting at byte 462.

## Flag

```text
flag{forensics_pdf_carve}
```

## Additional information

Opening the file in a text editor reveals text that appears, in summary, to describe an instruction directed at AI agents to visit a shortened link. Following it was not necessary to solve the challenge. It is speculated that it could be a distraction.

## Conclusions

It is important to examine the files we download, since a file's extension does not guarantee its actual format.
