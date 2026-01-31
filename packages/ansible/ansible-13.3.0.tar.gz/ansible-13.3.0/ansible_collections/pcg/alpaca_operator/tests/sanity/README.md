# Ansible Sanity Tests

This directory contains ignore files for Ansible sanity tests across different Ansible versions.

## Purpose

Ansible sanity tests are automated checks that validate code quality, documentation, and adherence to Ansible best practices. The ignore files in this directory specify which sanity test violations should be ignored for specific Ansible versions.

## Files

- `ignore-2.12.txt` - Ignore rules for Ansible 2.12
- `ignore-2.13.txt` - Ignore rules for Ansible 2.13
- `ignore-2.14.txt` - Ignore rules for Ansible 2.14
- `ignore-2.15.txt` - Ignore rules for Ansible 2.15
- `ignore-2.16.txt` - Ignore rules for Ansible 2.16
- `ignore-2.17.txt` - Ignore rules for Ansible 2.17
- `ignore-2.18.txt` - Ignore rules for Ansible 2.18
- `ignore-2.19.txt` - Ignore rules for Ansible 2.19

## Content

The ignore files contain entries for:
- **PEP8 violations**: Code style issues that are intentionally kept for readability
- **Documentation validation**: Module documentation issues that are handled differently by design
- **License validation**: Apache-2.0 license usage instead of GPLv3

## Usage

These files are automatically used by Ansible's sanity test framework when running:
```bash
ansible-test sanity
```

Each file corresponds to a specific Ansible version and contains the same ignore rules, ensuring consistent behavior across supported Ansible versions.