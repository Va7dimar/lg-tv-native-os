# Repro appendix — adaptation libkadaptor inspection (for later Page merge)

Do not treat this as a Page or ledger update.

1. Confirm reviewed hashes:
   - `tooling/adaptation_libkadaptor_phase.py` `7884236467e1533de7e3ac1266c602845cee35f4acbda11612d7e01dd36842c2`
   - `tooling/isolate_adaptation_phase.py` `192dce045e47c30379e35e66584f6d21b584ecf6418a9729d1d334777730e55b`
2. Require a fresh output directory (this run used `inspection-adaptation-PENDING-REVIEW` when absent). It now exists: DO NOT reuse, delete or overwrite it. This is a freshness requirement, not permission to test collision behavior or retry the cap-stopped phase.
3. One command:
   `python3 /workspace/lg-tv/tooling/isolate_adaptation_phase.py --outer '/workspace/lg-tv/tvs/lg-65nano756pr/sources/catalog/archives/webOS 6.0 KLP_1.0_2.tar.gz' --output-dir /workspace/lg-tv/tvs/lg-65nano756pr/sources/catalog/inspection-adaptation-PENDING-REVIEW`
4. Count success only if exit 0 and `phase.json` has `ok=true`, `status=ok`, and `copied[0].verified_before_inner=true`. This execution: exit 1, `status=partial`, `max_selected_combined_bytes exceeded`, copy pin still matched.
5. Analyze only `phase.json` metadata plus `selected/` plaintext; this cap-stopped phase is not to be retried or resumed, and no more libkadaptor parsing or selection follows it. Current work analyzes admitted generated data only.
