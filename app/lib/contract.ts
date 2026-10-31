import { z } from "zod";

export const scheduleSchema = z.object({
  id: z.string().regex(/^[A-Za-z0-9_-]{1,32}$/),
  medication: z.string().trim().min(1).max(80),
  time: z.string().regex(/^([01][0-9]|2[0-3]):[0-5][0-9]$/),
  compartment: z.number().int().min(1).max(6),
  enabled: z.boolean(),
  auth_user_id: z.number().int().min(1).max(1000),
}).strict();

export const configSchema = z.object({
  revision: z.number().int().min(0).max(4294967295),
  timezone: z.literal("Asia/Kolkata"),
  schedules: z.array(scheduleSchema.omit({ medication: true })).max(32),
}).strict();

export const updateSchema = z.object({
  expected_revision: z.number().int().min(0).max(4294967294),
  timezone: z.literal("Asia/Kolkata"),
  schedules: z.array(scheduleSchema).max(32),
}).strict();

const eventSchema = z.object({
  event_id: z.string(),
  schedule_id: z.string().nullable(),
  dose_id: z.string().nullable(),
  event: z.enum(["dispensed", "missed", "error"]),
  received_at: z.string().datetime({ offset: true }),
  occurred_at: z.null(),
  reason: z.string().nullable(),
  simulated: z.boolean(),
});

export const dashboardSchema = z.object({
  device_id: z.string(),
  revision: z.number().int(),
  timezone: z.literal("Asia/Kolkata"),
  schedules: z.array(scheduleSchema),
  status: z.object({
    desired_revision: z.number().int(),
    applied_revision: z.number().int(),
    synchronized: z.boolean(),
    last_config_result: z.object({
      revision: z.number().int(),
      status: z.enum(["applied", "deferred", "rejected"]),
      reason: z.string(),
    }).nullable(),
  }),
  events: z.array(eventSchema),
  notifications: z.array(z.object({ event_id: z.string(), status: z.literal("simulated") })),
});

export type Schedule = z.infer<typeof scheduleSchema>;
export type DoseEvent = z.infer<typeof eventSchema>;
export type Dashboard = z.infer<typeof dashboardSchema>;
export type ConfigUpdate = z.infer<typeof updateSchema>;
