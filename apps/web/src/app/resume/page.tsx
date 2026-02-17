"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";

import { ResumeParseStatus } from "@/types/resume";

const uploadSchema = z.object({
  file: z
    .any()
    .refine((value) => value?.length === 1, "请上传 1 个简历文件")
    .refine((value) => {
      const file = value?.[0] as File | undefined;
      if (!file) {
        return false;
      }
      return ["application/pdf", "application/msword", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"].includes(
        file.type
      );
    }, "仅支持 PDF 或 Word 文件")
});

type UploadForm = z.infer<typeof uploadSchema>;

export default function ResumePage(): JSX.Element {
  const [status, setStatus] = useState<ResumeParseStatus>("idle");
  const form = useForm<UploadForm>({ resolver: zodResolver(uploadSchema) });
  const statusLabel: Record<ResumeParseStatus, string> = {
    idle: "待处理",
    processing: "解析中",
    success: "成功",
    failure: "失败"
  };

  const submit = form.handleSubmit(async () => {
    setStatus("processing");
    await new Promise((resolve) => setTimeout(resolve, 1200));
    setStatus("success");
  });

  return (
    <div className="space-y-4">
      <header>
        <h1 className="text-2xl font-black text-brand-700">简历上传（阶段二占位）</h1>
        <p className="text-sm text-slate-600">
          该页面已预留简历解析接入，当前为占位流程（Mock）。
        </p>
      </header>

      <form className="card max-w-xl space-y-4" onSubmit={submit}>
        <label>
          <span className="mb-1 block text-sm font-semibold">上传简历</span>
          <input type="file" className="input pt-2" accept=".pdf,.doc,.docx" {...form.register("file")} />
        </label>

        {form.formState.errors.file ? (
          <p className="text-sm text-red-600">{form.formState.errors.file.message as string}</p>
        ) : null}

        <button type="submit" className="btn-primary">
          开始解析
        </button>

        <div className="rounded-lg border border-brand-100 bg-brand-50 p-3 text-sm text-slate-700">
          <p>状态: {statusLabel[status]}</p>
          {status === "processing" ? <p className="mt-1">解析中...</p> : null}
          {status === "success" ? <p className="mt-1">解析完成（Mock），后续将展示结构化结果。</p> : null}
          {status === "failure" ? <p className="mt-1">解析失败（Mock），请重试。</p> : null}
        </div>
      </form>
    </div>
  );
}
