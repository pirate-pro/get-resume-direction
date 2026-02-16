"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";

import { ResumeParseStatus } from "@/types/resume";

const uploadSchema = z.object({
  file: z
    .any()
    .refine((value) => value?.length === 1, "Please upload one resume file")
    .refine((value) => {
      const file = value?.[0] as File | undefined;
      if (!file) {
        return false;
      }
      return ["application/pdf", "application/msword", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"].includes(
        file.type
      );
    }, "Only PDF or Word files are supported")
});

type UploadForm = z.infer<typeof uploadSchema>;

export default function ResumePage(): JSX.Element {
  const [status, setStatus] = useState<ResumeParseStatus>("idle");
  const form = useForm<UploadForm>({ resolver: zodResolver(uploadSchema) });

  const submit = form.handleSubmit(async () => {
    setStatus("processing");
    await new Promise((resolve) => setTimeout(resolve, 1200));
    setStatus("success");
  });

  return (
    <div className="space-y-4">
      <header>
        <h1 className="text-2xl font-black text-brand-700">Resume Upload (Phase 2 Placeholder)</h1>
        <p className="text-sm text-slate-600">
          This page is prepared for backend resume parsing integration. Current behavior is mock-only.
        </p>
      </header>

      <form className="card max-w-xl space-y-4" onSubmit={submit}>
        <label>
          <span className="mb-1 block text-sm font-semibold">Upload resume</span>
          <input type="file" className="input pt-2" accept=".pdf,.doc,.docx" {...form.register("file")} />
        </label>

        {form.formState.errors.file ? (
          <p className="text-sm text-red-600">{form.formState.errors.file.message as string}</p>
        ) : null}

        <button type="submit" className="btn-primary">
          Parse Resume
        </button>

        <div className="rounded-lg border border-brand-100 bg-brand-50 p-3 text-sm text-slate-700">
          <p>Status: {status}</p>
          {status === "processing" ? <p className="mt-1">Parsing in progress...</p> : null}
          {status === "success" ? <p className="mt-1">Parse complete (mock). Structured data preview is planned.</p> : null}
          {status === "failure" ? <p className="mt-1">Parse failed (mock). Try again.</p> : null}
        </div>
      </form>
    </div>
  );
}
