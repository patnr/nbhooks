@test "nbhooks command exists" {
  nbhooks
  [ $? -eq 0 ]
}
