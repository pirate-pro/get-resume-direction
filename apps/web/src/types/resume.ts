export type ResumeParseStatus = "idle" | "processing" | "success" | "failure";

export interface ResumeParseResult {
  parse_status: ResumeParseStatus;
  parsed_fields?: {
    education?: string[];
    skills?: string[];
    expected_city?: string;
    expected_role?: string;
  };
}
