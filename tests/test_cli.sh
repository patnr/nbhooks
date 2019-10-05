@test "nb-ensure-clean command exists" {
  nb-ensure-clean
  [ $? -eq 0 ]
}
