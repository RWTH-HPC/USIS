# Task: check whether from_nr(i) = to_nr(i-1) + 1
#       with i = number of the line in the input file
#
# Input:
# task version file from_nr to_nr
# $1   $2      $3   $4      $5
#
BEGIN{
  last_task = " "; 
  last_vers = " ";
  last_file = " "; 
  last_from = 0;
  last_to   = 0;
  part      = " ";
}
{
  if ($1 == "FILELENGTH") 
  {
    part = "FILELENGTH";
  }
  else if ($1 == "USED_SECTIONS")
  {
    part = "USED_SECTIONS";
  }
  else if (part == "FILELENGTH")
  {
    lng[$2] = $1; 
  }
  else
  { 
#   ... in checking USED_SECTIONS ...
    full_filename = "from_"$2"/"$3;
    if ($3 != last_file)
    {
      if (last_file != " ")
      {
#       ... finish checking of an old file 
#       ... last_to should be identical to line count 
        line_count = lng [ last_full ];
        if (line_count != last_to) 
        { 
          printf ("\n"); 
          printf ("%8s %3s %16s %4d %4d (last_to) != %d (line_count)\n", last_task, last_vers, last_file, last_from, last_to, line_count); 
        } 
      } 
#     ... start checking a new file 
      last_task = " "; 
      last_vers = " ";
      last_file = " "; 
      last_full = " "; 
      last_from = 0;
      last_to   = 0;
    } 
    if ($4 != (last_to + 1)) 
    {
      printf ("\n"); 
      printf ("%8s %3s %16s %4d %4d\n", last_task, last_vers, last_file, last_from, last_to); 
      printf ("%8s %3s %16s %4d %4d\n", $1, $2, $3, $4, $5); 
    } 
    last_task = $1; 
    last_vers = $2;
    last_file = $3; 
    last_full = full_filename;
    last_from = $4;
    last_to   = $5;
  } 
} 
